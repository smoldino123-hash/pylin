#!/usr/bin/env python3
"""Combine project files into a single text file.

This mirrors the behavior of the Node.js script provided by the user:
- recursively collect files
- skip .git and excluded paths
- skip .log and .txt files
- write all content blocks to one output file
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

try:
    from .utils import is_excluded
except Exception:
    from utils import is_excluded


def collect_files(root_dir: Path, current_dir: Path | None = None, output: List[Path] | None = None) -> List[Path]:
    if current_dir is None:
        current_dir = root_dir
    if output is None:
        output = []

    try:
        entries = list(current_dir.iterdir())
    except Exception:
        return output

    for entry in entries:
        full_path = entry

        if entry.name == ".git":
            continue

        if is_excluded(str(full_path), entry.name):
            continue

        if entry.is_dir():
            collect_files(root_dir, full_path, output)
            continue

        if entry.is_file():
            extension = entry.suffix.lower()
            if extension in {".log", ".txt"}:
                continue
            output.append(full_path)

    return output


def combine_project_code(root_dir: Path | None = None, output_file: Path | None = None) -> Path:
    if root_dir is None:
        root_dir = Path.cwd()
    else:
        root_dir = root_dir.resolve()

    if output_file is None:
        output_file = root_dir / "combined-code.txt"
    else:
        output_file = output_file.resolve()

    files = collect_files(root_dir)
    sorted_files = sorted(
        [file_path for file_path in files if file_path.resolve() != output_file],
        key=lambda value: str(value),
    )

    chunks: List[str] = []

    for file_path in sorted_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as err:
            content = f"[Unable to read file: {err}]"

        chunks.append(f"FILE: {file_path.relative_to(root_dir)}")
        chunks.append("```")
        chunks.append(content.replace("\r\n", "\n"))
        chunks.append("```")
        chunks.append("")

    final_output = "\n".join(chunks).rstrip("\n") + "\n"
    output_file.write_text(final_output, encoding="utf-8")

    print(f"Combined {len(sorted_files)} files into {output_file}")
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine project files into one text file")
    parser.add_argument("root_dir", nargs="?", default=None, help="Root directory to scan")
    parser.add_argument("output_file", nargs="?", default=None, help="Output text file path")
    args = parser.parse_args()

    root_dir = Path(args.root_dir).resolve() if args.root_dir else Path.cwd()
    output_file = Path(args.output_file).resolve() if args.output_file else root_dir / "combined-code.txt"

    try:
        combine_project_code(root_dir, output_file)
    except Exception as err:
        print(f"Failed to combine project code: {err}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
