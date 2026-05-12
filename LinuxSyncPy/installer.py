"""Installer helpers for pip and npm operations."""
from pathlib import Path
from typing import Iterable, Union
import logging

from .utils import (
    add_to_package_json,
    append_to_file,
    resolve_npm_dependency_spec,
    run_silent,
    run_and_capture,
    _log_debug,
)


def ensure_gdown_installed(dry_run: bool = False) -> None:
    logger = logging.getLogger('linuxsyncpy.installer')
    if dry_run:
        logger.debug('ensure_gdown_installed dry_run=True, skipping install')
        return

    try:
        import gdown  # noqa: F401
        return
    except Exception:
        pass
    _log_debug('ensure_gdown_installed: gdown not found, attempting pip install')
    logger.debug('ensure_gdown_installed gdown import failed, invoking pip install')
    try:
        code, out, err = run_and_capture('pip install --upgrade gdown', cwd=str(Path.cwd()))
        _log_debug(f'pip install gdown returncode={code} stdout={out.strip()!r} stderr={err.strip()!r}')
        logger.debug(f'ensure_gdown_installed pip result returncode={code}')
        if code != 0:
            raise RuntimeError(f'pip install returned non-zero exit code: {code}')
    except Exception as exc:
        _log_debug(f'ensure_gdown_installed failed: {exc}')
        logger.exception(f'ensure_gdown_installed failed: {exc}')
        raise


def install_pip_with_package(requirements_path: Union[str, Path], package: str, dry_run: bool = False) -> None:
    logger = logging.getLogger('linuxsyncpy.installer')
    req_path = Path(requirements_path)
    logger.debug(f'install_pip_with_package start requirements_path={req_path} package={package} dry_run={dry_run}')
    req_path.parent.mkdir(parents=True, exist_ok=True)
    if not req_path.exists():
        req_path.write_text('', encoding='utf-8')

    append_to_file(str(req_path), package)

    if dry_run:
        return

    run_silent(f'pip install -r "{req_path}"', cwd=str(req_path.parent))


def install_pip_with_packages(requirements_path: Union[str, Path], package_names: Iterable[str], dry_run: bool = False) -> None:
    logger = logging.getLogger('linuxsyncpy.installer')
    req_path = Path(requirements_path)
    package_names = list(package_names)
    logger.debug(f'install_pip_with_packages start requirements_path={req_path} packages={package_names} dry_run={dry_run}')
    req_path.parent.mkdir(parents=True, exist_ok=True)
    if not req_path.exists():
        req_path.write_text('', encoding='utf-8')

    for package_name in package_names:
        append_to_file(str(req_path), package_name)

    if dry_run:
        return

    run_silent(f'pip install -r "{req_path}"', cwd=str(req_path.parent))


def install_npm_with_package(package_json_path: Union[str, Path], package_name, version: str = '*', dry_run: bool = False) -> None:
    logger = logging.getLogger('linuxsyncpy.installer')
    pkg_path = Path(package_json_path)
    logger.debug(f'install_npm_with_package start package_json_path={pkg_path} package_name={package_name} version={version} dry_run={dry_run}')
    if not pkg_path.exists():
        logger.debug(f'install_npm_with_package skipped missing package_json_path={pkg_path}')
        return

    spec = resolve_npm_dependency_spec(package_name, version)
    add_to_package_json(str(pkg_path), spec['name'], spec['spec'])

    if dry_run:
        return

    run_silent('npm install', cwd=str(pkg_path.parent))


def install_npm_with_packages(package_json_path: Union[str, Path], package_names, version: str = '*', dry_run: bool = False) -> None:
    logger = logging.getLogger('linuxsyncpy.installer')
    pkg_path = Path(package_json_path)
    package_names = list(package_names)
    logger.debug(f'install_npm_with_packages start package_json_path={pkg_path} packages={package_names} version={version} dry_run={dry_run}')
    if not pkg_path.exists():
        logger.debug(f'install_npm_with_packages skipped missing package_json_path={pkg_path}')
        return

    for package_name in package_names:
        spec = resolve_npm_dependency_spec(package_name, version)
        add_to_package_json(str(pkg_path), spec['name'], spec['spec'])

    if dry_run:
        return

    run_silent('npm install', cwd=str(pkg_path.parent))


def download_via_gdown(drive_id: str, output_path: str):
    logger = logging.getLogger('linuxsyncpy.installer')
    logger.debug(f'download_via_gdown starting drive_id={drive_id} output_path={output_path}')
    try:
        code, out, err = run_and_capture(f'python -m gdown "{drive_id}" -O "{output_path}"', cwd=str(Path.cwd()))
        _log_debug(f'gdown returncode={code} stdout={out.strip()!r} stderr={err.strip()!r}')
        logger.debug(f'download_via_gdown completed drive_id={drive_id} returncode={code} output_exists={Path(output_path).exists()}')
        if Path(output_path).exists():
            logger.debug(f'downloaded file exists at {output_path}')
            return output_path
        _log_debug(f'Download did not produce file at {output_path}')
        return None
    except Exception as err:
        _log_debug(f'gdown download failed: {err}')
        _log_debug(__import__('traceback').format_exc().rstrip())
        return None


installPipWithPackage = install_pip_with_package
installPipWithPackages = install_pip_with_packages
installNpmWithPackage = install_npm_with_package
installNpmWithPackages = install_npm_with_packages
downloadViaGdown = download_via_gdown
ensureGdownInstalled = ensure_gdown_installed
