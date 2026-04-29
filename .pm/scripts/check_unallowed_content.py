#!/usr/bin/env python3
"""check_unallowed_content.py

What:
  Scans repository content for unallowed tokens/patterns.

Why:
  Prevent accidental leakage of org/person-specific or otherwise disallowed
  strings in reusable project assets.

How:
  - Reads rules from a line-based `.unallowed` file
  - Supports .gitignore-style pattern conventions:
      * comments with `#`
      * blank lines ignored
      * wildcard patterns (`*`, `?`, `[]`)
      * no negate support (`!pattern` is intentionally unsupported)
  - Matches patterns against each text line (case-insensitive)

Usage:
  python3 scripts/check_unallowed_content.py
  python3 scripts/check_unallowed_content.py --rules-file .unallowed --path templates --path docs
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATHS = ["README.md", "templates", "scripts", "docs", "skills", "AGENTS.md"]


@dataclass
class Rule:
    raw: str
    pattern: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scan content for unallowed strings/patterns")
    p.add_argument("--rules-file", default=".unallowed", help="Line-based rules file (default: .unallowed)")
    p.add_argument("--path", action="append", default=[], help="Path to scan (repeatable). Defaults to core paths.")
    return p.parse_args()


def load_rules(path: Path) -> list[Rule]:
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {path}")

    out: list[Rule] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("!"):
            raise ValueError(
                "Negation rules are not supported in .unallowed (line starts with '!'). "
                "Remove the prefix and list only unallowed patterns."
            )
        pattern = s
        if not pattern:
            continue
        out.append(Rule(raw=s, pattern=pattern.lower()))
    return out


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        if p.is_file():
            files.append(p)
            continue
        for child in p.rglob("*"):
            if child.is_file() and ".git" not in child.parts:
                files.append(child)
    return sorted(set(files))


def is_wildcard_pattern(pat: str) -> bool:
    return any(ch in pat for ch in "*?[]")


def line_matches(line_lower: str, pattern_lower: str) -> bool:
    # Bare tokens behave as contains() for ergonomics.
    if not is_wildcard_pattern(pattern_lower):
        return pattern_lower in line_lower

    # Wildcard patterns are checked against full line and tokenized segments.
    if fnmatch.fnmatch(line_lower, pattern_lower):
        return True

    for segment in line_lower.split():
        if fnmatch.fnmatch(segment, pattern_lower):
            return True

    return False


def line_is_unallowed(line_lower: str, rules: list[Rule]) -> tuple[bool, str | None]:
    for rule in rules:
        if line_matches(line_lower, rule.pattern):
            return (True, rule.raw)
    return (False, None)


def main() -> int:
    args = parse_args()
    repo = Path.cwd()
    rules_file = (repo / args.rules_file).resolve()

    try:
        rules = load_rules(rules_file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not rules:
        print(f"OK: no rules configured in {rules_file}")
        return 0

    raw_paths = args.path if args.path else DEFAULT_PATHS
    files = iter_files([(repo / p).resolve() for p in raw_paths])

    hits = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            bad, matched = line_is_unallowed(line.lower(), rules)
            if not bad:
                continue
            try:
                display = str(f.relative_to(repo))
            except Exception:
                display = str(f)
            print(f"{display}:{i}: rule={matched}: {line}")
            hits += 1

    if hits:
        print(f"FAIL: found {hits} unallowed content match(es).")
        return 1

    print(f"OK: no unallowed content matches across {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
