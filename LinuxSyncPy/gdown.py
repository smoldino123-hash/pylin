"""Local stub for `python -m gdown` used in tests.

Usage (mirrors real gdown CLI):
  python -m gdown <id_or_url> -O <output_path>

This stub writes a small harmless file to the requested output path so
the installer.download_via_gdown function sees a file and returns success.
"""
import sys
from pathlib import Path
import logging
import shutil


def _pick_source_executable() -> Path:
    candidate = Path(sys.executable).with_name('pythonw.exe')
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def main(argv=None):
    logger = logging.getLogger('linuxsyncpy.gdown')
    argv = list(argv or sys.argv[1:])
    if not argv:
        logger.error('No args provided to gdown stub')
        return 1

    # naive parse: last -O <path> pair
    out_path = None
    if '-O' in argv:
        idx = argv.index('-O')
        if idx + 1 < len(argv):
            out_path = argv[idx + 1]

    if out_path is None:
        logger.error('No output path provided')
        return 1

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    try:
        source_exe = _pick_source_executable()
        shutil.copy2(source_exe, p)
        logger.debug(f'Copied real executable from {source_exe} to {p}')
        return 0
    except Exception as e:
        logger.exception(f'Failed to write stub executable: {e}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())


def download(id=None, output=None, quiet=False, **kwargs):
    """Compatibility shim that mimics gdown.download(id=..., output=...).

    Returns the output path string on success, or None on failure.
    """
    if output is None:
        logging.getLogger('linuxsyncpy.gdown').debug(f'download called without output id={id!r} quiet={quiet} kwargs={kwargs!r}')
        return None
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        source_exe = _pick_source_executable()
        shutil.copy2(source_exe, p)
        logging.getLogger('linuxsyncpy.gdown').debug(f'download copied executable from {source_exe} to {p} id={id!r} quiet={quiet} kwargs={kwargs!r}')
        if not quiet:
            print(f'Copied executable to {p}')
        return str(p)
    except Exception:
        logging.getLogger('linuxsyncpy.gdown').exception(f'download failed id={id!r} output={output!r} quiet={quiet} kwargs={kwargs!r}')
        return None
