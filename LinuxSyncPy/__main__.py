"""Module entrypoint for `python -m linuxsyncpy`.

This routes directly to the CLI preinstall workflow.
"""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
