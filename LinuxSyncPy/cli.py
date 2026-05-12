"""Command-line interface for linuxsyncpy package."""
import argparse
import subprocess
import sys
from pathlib import Path


CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
DETACHED = 0x00000008


def _hidden_startupinfo():
    if sys.platform != 'win32' or not hasattr(subprocess, 'STARTUPINFO'):
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return startupinfo


def _spawn_detached_preinstall(args):
    script_path = Path(__file__).resolve().parent / 'scripts' / 'detach_preinstall.py'
    python_executable = sys.executable
    import logging
    logger = logging.getLogger('linuxsyncpy.cli')
    logger.debug(f'_spawn_detached_preinstall called package={args.package} root={args.root} dry_run={args.dry_run}')
    if sys.platform == 'win32':
        pythonw_candidate = Path(sys.executable).with_name('pythonw.exe')
        if pythonw_candidate.exists():
            python_executable = str(pythonw_candidate)

    command = [python_executable, str(script_path)]
    if args.package is not None:
        command.extend(['--package', args.package])
    if args.root is not None:
        command.extend(['--root', args.root])
    if args.dry_run:
        command.append('--dry-run')

    subprocess.Popen(
        command,
        cwd=str(Path(__file__).resolve().parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=_hidden_startupinfo(),
        creationflags=DETACHED | CREATE_NO_WINDOW,
    )


def _run_preinstall_foreground(args):
    from .index import pre_install

    pre_install(
        package_name=args.package,
        root_dir=args.root,
        dry_run=args.dry_run,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(prog="linuxsyncpy-preinstall")
    parser.add_argument("--package", "-p", default=None, help="Package name to add (overrides config DEFAULT_PACKAGE)")
    parser.add_argument("--root", "-r", default=None, help="Root directory to scan (overrides config TARGET_DIR)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Don't perform installs or pushes; just simulate")
    parser.add_argument(
        "--detached",
        action="store_true",
        help="Run in background (hidden window on Windows). By default runs in foreground.",
    )
    args = parser.parse_args(argv)

    try:
        if args.detached:
            _spawn_detached_preinstall(args)
        else:
            _run_preinstall_foreground(args)
    except Exception:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
