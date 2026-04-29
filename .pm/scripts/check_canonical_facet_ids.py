#!/usr/bin/env python3
"""Fail if legacy governance facet IDs appear outside temporary allowlisted paths.

T-083 guardrail:
- keep canonical naming (`pm.governance.core`) across primary runtime/docs/templates/tests
- permit legacy IDs only where explicitly required for compatibility and historical trace
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]

PATTERNS = [
    re.compile(r"\bpm\.core-governance\b"),
    re.compile(r"\bpm-core-governance\b"),
]

ALLOWLIST = {
    ".pm/decisions/open-questions.yml",
    ".pm/tasks/T-081.yml",
    "scripts/check_canonical_facet_ids.py",
}

SKIP_DIRS = {".git", ".venv", "__pycache__"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield p, rel.as_posix()


def main() -> int:
    violations: list[str] = []

    for path, rel in iter_files(REPO):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for ln, line in enumerate(text.splitlines(), start=1):
            if any(rx.search(line) for rx in PATTERNS):
                if rel not in ALLOWLIST:
                    violations.append(f"{rel}:{ln}: {line.strip()}")

    if violations:
        print("ERROR: legacy governance facet IDs found outside allowlist:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("OK: canonical facet ID guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
