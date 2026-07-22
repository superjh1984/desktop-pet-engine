#!/usr/bin/env python3
"""Copy the bundled desktop-pet template into a new clean project."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "desktop-pet-engine"
TEXT_SUFFIXES = {".md", ".swift", ".json", ".plist", ".sh", ".py"}


def replace_text(root: Path, app_name: str, bundle_id: str) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            value = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = value.replace("桌宠引擎", app_name).replace(
            "io.github.example.desktop-pet-engine", bundle_id
        )
        if updated != value:
            path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--app-name", default="桌宠引擎")
    parser.add_argument("--bundle-id", default="io.github.example.desktop-pet-engine")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", args.bundle_id):
        parser.error("--bundle-id must use reverse-DNS form")
    if not args.app_name.strip():
        parser.error("--app-name cannot be empty")

    target = args.target.expanduser().resolve()
    if target.exists():
        parser.error(f"target already exists: {target}")
    if not TEMPLATE.is_dir():
        parser.error(f"template is missing: {TEMPLATE}")

    shutil.copytree(
        TEMPLATE,
        target,
        ignore=shutil.ignore_patterns(".build", "dist", ".DS_Store"),
    )
    replace_text(target, args.app_name.strip(), args.bundle_id)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

