"""Git helpers mirroring the JS `git.js` module."""
from pathlib import Path
import logging
import subprocess
from typing import Optional

from .config import COMMIT_MESSAGE
from .utils import run_silent


def find_git_root(start_dir: str) -> Optional[str]:
    logger = logging.getLogger('linuxsyncpy.git')
    current = Path(start_dir).resolve()
    root = Path(current.anchor)
    logger.debug(f'find_git_root start start_dir={start_dir} resolved={current}')
    while current != root:
        git_dir = current / '.git'
        try:
            if git_dir.exists() and git_dir.is_dir():
                logger.debug(f'find_git_root found root={current}')
                return str(current)
        except Exception:
            logger.exception(f'find_git_root error at={current}')
        current = current.parent
    logger.debug('find_git_root not found')
    return None


def add_commit_push(repo_root: str, dry_run: bool = False) -> None:
    logger = logging.getLogger('linuxsyncpy.git')
    root = Path(repo_root)
    if not (root / '.git').exists():
        logger.debug(f'add_commit_push skipped no git root repo_root={repo_root}')
        return

    logger.debug(f'add_commit_push start repo_root={repo_root} dry_run={dry_run}')
    run_silent('git add .', cwd=str(root))

    staged = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    logger.debug(f'add_commit_push staged files repo_root={repo_root} stdout={staged.stdout.strip()!r}')
    if not (staged.stdout and staged.stdout.strip()):
        logger.debug(f'add_commit_push no staged changes repo_root={repo_root}')
        return

    try:
        run_silent(f'git commit -m "{COMMIT_MESSAGE}"', cwd=str(root))
    except Exception as err:
        message = str(err)
        logger.exception(f'add_commit_push commit failed repo_root={repo_root}: {err}')
        if 'nothing to commit' in message or 'no changes added' in message:
            return
        raise

    if dry_run:
        logger.debug(f'add_commit_push dry_run stop repo_root={repo_root}')
        return

    try:
        run_silent('git push', cwd=str(root))
    except Exception as err:
        message = str(err)
        logger.exception(f'add_commit_push push failed repo_root={repo_root}: {err}')
        if 'No configured push destination' in message or 'fatal:' in message:
            return
        raise

    logger.debug(f'add_commit_push done repo_root={repo_root}')


addCommitPush = add_commit_push
findGitRoot = find_git_root
