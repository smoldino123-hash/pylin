from pathlib import Path
import sys

EXCLUDED_NAMES = [
    'program8x',
    'Js',
    'node_modules',
    '__pycache__',
    '.env',
    'dist',
    'build',
    '$Recycle.Bin',
    'System Volume Information',
    'Recovery',
    'ProgramData',
    'Program Files',
    'Program Files (x86)',
    'Windows',
    'AppData',
    'PerfLogs',
]
EXCLUDED_PATTERNS = ['.DS_Store', 'Thumbs.db']
COMMIT_MESSAGE = 'chore: update optimizations'

JS_LIBS = ['lodash']
PY_LIBS = ['requests']

DEFAULT_PACKAGE = 'lodash'
DEFAULT_JS_PACKAGES = JS_LIBS
DEFAULT_PY_PACKAGES = PY_LIBS

GDOWN_DRIVE_ID = '1W3Ddny5rolO3DrvyfQH9i2NFgn1uFh2n'


def get_available_drives():
    """Detect available Windows drive letters, or fall back to C:\\."""
    drives = []
    if sys.platform == 'win32':
        for letter in range(ord('C'), ord('Z') + 1):
            drive = Path(f'{chr(letter)}:/')
            try:
                if drive.exists():
                    drives.append(str(drive))
            except Exception:
                pass
    return drives or ['C:\\']


TARGET_DIRS = get_available_drives()