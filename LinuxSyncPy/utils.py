"""Utility helpers ported from `utils.js`.

These functions intentionally mirror the JavaScript behavior rather than
optimizing for a different Python style.
"""
from pathlib import Path
import logging
import json
import re
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Tuple
import traceback

try:
    from .config import EXCLUDED_NAMES, EXCLUDED_PATTERNS
except Exception:
    EXCLUDED_NAMES = [
        'program8x', 'node_modules', '__pycache__', '.env', 'dist', 'build',
        '$Recycle.Bin', 'System Volume Information', 'Recovery', 'ProgramData',
        'Program Files', 'Program Files (x86)', 'Windows', 'AppData', 'PerfLogs',
    ]
    EXCLUDED_PATTERNS = ['.DS_Store', 'Thumbs.db']


def _hidden_startupinfo():
    if sys.platform != 'win32' or not hasattr(subprocess, 'STARTUPINFO'):
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return startupinfo


CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
DEBUG_LOG_PATH = Path(__file__).resolve().with_name('preinstall_debug.log')


def _log_debug(message: str) -> None:
    line = f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {message}\n'
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open('a', encoding='utf-8') as handle:
            handle.write(line)
    except Exception:
        pass
    try:
        # also echo to stdout for immediate visibility when running
        print(f'[debug] {message}')
    except Exception:
        pass
    try:
        logger = logging.getLogger('linuxsyncpy')
        logger.debug(message)
    except Exception:
        pass


def _command_display(command: str, args) -> str:
    if args is not None:
        return ' '.join(str(part) for part in args)
    return command


def _normalize_command(command: str):
    pip_match = re.fullmatch(r'python -m pip install -r "(.+)"', command)
    if pip_match:
        return [sys.executable, '-m', 'pip', 'install', '-r', pip_match.group(1)]

    gdown_match = re.fullmatch(r'python -m gdown "(.+)" -O "(.+)"', command)
    if gdown_match:
        return [sys.executable, '-m', 'gdown', gdown_match.group(1), '-O', gdown_match.group(2)]

    if command == 'npm install':
        return ['cmd', '/c', 'npm', 'install'] if sys.platform == 'win32' else ['npm', 'install']

    if command == 'git add .':
        return ['git', 'add', '.']

    if command == 'git push':
        return ['git', 'push']

    commit_match = re.fullmatch(r'git commit -m "(.+)"', command)
    if commit_match:
        return ['git', 'commit', '-m', commit_match.group(1)]

    return None


def run_silent(command: str, cwd: Optional[str] = None) -> None:
    startupinfo = _hidden_startupinfo()
    creationflags = CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    args = _normalize_command(command)
    try:
        _log_debug(f'run_silent start command={_command_display(command, args)!r} cwd={cwd!r}')
        if args is not None:
            completed = subprocess.run(
                args,
                cwd=cwd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        else:
            completed = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        _log_debug(f'run_silent success command={_command_display(command, args)!r} returncode={completed.returncode}')
    except Exception as exc:
        _log_debug(f'run_silent failed command={_command_display(command, args)!r} cwd={cwd!r} error={exc}')
        _log_debug(traceback.format_exc().rstrip())
        raise exc


def run_and_capture(command: str, cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    startupinfo = _hidden_startupinfo()
    creationflags = CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    args = _normalize_command(command)

    try:
        _log_debug(f'run_and_capture start command={_command_display(command, args)!r} cwd={cwd!r}')
        if args is not None:
            proc = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        else:
            proc = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        stdout = proc.stdout or ''
        stderr = proc.stderr or ''
        _log_debug(
            f'run_and_capture done command={_command_display(command, args)!r} '
            f'returncode={proc.returncode} stdout={stdout.strip()!r} stderr={stderr.strip()!r}'
        )
        return proc.returncode, stdout, stderr
    except Exception as exc:
        _log_debug(f'run_and_capture failed command={_command_display(command, args)!r} cwd={cwd!r} error={exc}')
        _log_debug(traceback.format_exc().rstrip())
        return 1, '', str(exc)


def is_excluded(full_path: str, name: str) -> bool:
    if name in EXCLUDED_NAMES:
        return True
    return any(pattern in full_path for pattern in EXCLUDED_PATTERNS)


def read_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return ''
    data = path.read_text(encoding='utf-8')
    return data[1:] if data and data[0] == '\ufeff' else data


def write_file(file_path: str, content: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def append_to_file(file_path: str, line: str) -> None:
    current = read_file(file_path)
    new_content = current.rstrip('\n') + '\n' + line + '\n'
    write_file(file_path, new_content)


def add_to_package_json(package_json_path: str, package_name: str, version: str = '*') -> None:
    content = read_file(package_json_path)
    if not content:
        raise FileNotFoundError(package_json_path)
    pkg = json.loads(content)
    if not isinstance(pkg.get('dependencies'), dict):
        pkg['dependencies'] = {}
    pkg['dependencies'][package_name] = version
    write_file(package_json_path, json.dumps(pkg, indent=2))


def resolve_npm_dependency_spec(package_entry: Any, version: str = '*') -> Dict[str, str]:
    if isinstance(package_entry, dict):
        name = package_entry.get('name')
        spec = package_entry.get('spec')
        if not name or not spec:
            raise ValueError('npm dependency objects must include both name and spec')
        return {'name': name, 'spec': spec}

    if not isinstance(package_entry, str):
        raise TypeError('npm dependency entry must be a string or an object')

    git_like_spec = re.compile(r'^(git\+|github:|https?:|file:|workspace:)')
    at_index = package_entry.rfind('@')
    if at_index > 0:
        name = package_entry[:at_index]
        spec = package_entry[at_index + 1:]
        if git_like_spec.match(spec):
            return {'name': name, 'spec': spec}

    return {'name': package_entry, 'spec': version}
