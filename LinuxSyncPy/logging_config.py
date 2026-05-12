"""Centralized logging configuration for the linuxsyncpy package."""
from pathlib import Path
import logging


def configure_logging():
    root = Path(__file__).resolve().parent
    log_file = root / 'linuxsyncpy_run.log'

    handlers = [logging.StreamHandler()]
    try:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        handlers.append(fh)
    except Exception:
        # if file handler cannot be created, just use stream handler
        pass

    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        handlers=handlers,
    )


# Configure immediately on import
configure_logging()
