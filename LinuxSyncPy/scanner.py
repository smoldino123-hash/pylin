"""Project scanner: locate git roots, package.json and requirements.txt files."""
from pathlib import Path
import logging
from typing import Dict, List

from .utils import is_excluded


def scan_project(root_dir: str = None) -> Dict[str, List[str]]:
    root = Path(root_dir or Path.cwd()).resolve()
    logger = logging.getLogger('linuxsyncpy.scanner')
    logger.debug(f'scan_project start root={root}')
    requirements_paths = []
    package_json_paths = []
    git_roots = set()

    def _scan(dir_path: Path, parent_has_git: bool = False):
        try:
            entries = list(dir_path.iterdir())
        except Exception:
            logger.exception(f'failed to list dir path={dir_path}')
            return

        logger.debug(f'scanning dir={dir_path} entries={len(entries)} parent_has_git={parent_has_git}')

        local_has_git = parent_has_git
        for entry in entries:
            name = entry.name
            full_path = str(entry)

            if entry.is_dir() and name == '.git':
                local_has_git = True
                git_roots.add(str(dir_path))
                logger.debug(f'found git root at={dir_path}')
                continue

            if is_excluded(full_path, name):
                logger.debug(f'excluded path={full_path}')
                continue

            if entry.is_dir():
                _scan(entry, local_has_git)
            elif entry.is_file():
                if name == 'package.json':
                    package_json_paths.append(full_path)
                    logger.debug(f'found package.json at={full_path}')
                elif name == 'requirements.txt':
                    requirements_paths.append(full_path)
                    logger.debug(f'found requirements.txt at={full_path}')

    _scan(root)

    logger.debug(
        'scan_project done '
        f'root={root} git_roots={len(git_roots)} package_json_paths={len(package_json_paths)} requirements_paths={len(requirements_paths)}'
    )

    return {
        'git_roots': list(git_roots),
        'package_json_paths': package_json_paths,
        'requirements_paths': requirements_paths,
    }


scanProject = scan_project
