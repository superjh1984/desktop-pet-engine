#!/usr/bin/env python3
"""Scan a candidate public release for common secrets and restricted terms."""

from __future__ import annotations

import argparse
import fnmatch
import re
from pathlib import Path


IGNORED_DIRS = {".git", ".build", "dist", "node_modules", "__pycache__"}
BLOCKED_FILES = (
    ".env",
    "*.p12",
    "*.mobileprovision",
    "*.provisionprofile",
    "*auth*qr*",
    "*.key",
)
TEXT_SUFFIXES = {
    "", ".md", ".txt", ".swift", ".json", ".plist", ".sh", ".py",
    ".yaml", ".yml", ".toml", ".xml", ".html", ".js", ".ts",
}
PATTERNS = {
    "absolute user path": re.compile(r"/(?:Users|Volumes)/[^\s\"']+"),
    "cloud signed URL": re.compile(r"(?:AccessKeyId|Signature|X-Amz-Signature)=", re.I),
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "API key assignment": re.compile(r"(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD)\s*[:=]\s*[\"']?[^\s\"']{8,}", re.I),
    "contact handle": re.compile(r"(?:wx|wechat|qq)\s*[:=]\s*[A-Za-z0-9_-]{4,}", re.I),
}


def is_ignored(path: Path, root: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.relative_to(root).parts[:-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--deny-term", action="append", default=[])
    args = parser.parse_args()

    root = args.path.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    findings: list[str] = []
    deny_terms = [term.casefold() for term in args.deny_term if term.strip()]
    for path in root.rglob("*"):
        if not path.is_file() or is_ignored(path, root):
            continue
        relative = path.relative_to(root)
        lower_name = path.name.casefold()
        if any(fnmatch.fnmatch(lower_name, pattern.casefold()) for pattern in BLOCKED_FILES):
            findings.append(f"blocked file: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")
        folded = text.casefold()
        for term in deny_terms:
            if term in folded:
                findings.append(f"restricted term {term!r}: {relative}")

    if findings:
        print("Public release audit failed:")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        return 1
    print(f"Public release audit passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

