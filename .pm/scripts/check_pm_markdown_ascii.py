#!/usr/bin/env python3
"""Guard: PM PM-authored docs/metadata should stay ASCII-safe.

Why: some terminals/pagers (for example `less` under non-UTF locales) may flag
files as binary-ish when smart punctuation appears. This guard keeps PM content
portable.

Scope:
- .pm/**/*.md
- .pm/tasks/**/*.yml
- templates/pm/.pm/**/*.md
- templates/pm/.pm/tasks/**/*.yml

Exclusions:
- .pm/inbox/raw/** (captured source content may include unicode)
"""

from __future__ import annotations

import argparse
from pathlib import Path

SCOPES = [".pm", "templates/pm/.pm"]
ALLOW_EXT = {".md", ".yml", ".yaml"}
EXCLUDE_SUBSTR = ["/.pm/inbox/raw/"]


def iter_targets(repo: Path):
    for scope in SCOPES:
        base = repo / scope
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in ALLOW_EXT:
                continue
            sp = str(p)
            if any(x in sp for x in EXCLUDE_SUBSTR):
                continue
            yield p


def find_non_ascii_lines(text: str):
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        chars = sorted({ch for ch in line if ord(ch) > 127})
        if chars:
            out.append((i, "".join(chars), line.strip()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check PM docs/tasks files for non-ASCII characters")
    ap.add_argument("repo", nargs="?", default=".", help="Repo root")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    failures = []

    for path in sorted(iter_targets(repo)):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            failures.append((path, [(0, "<decode-error>", str(e))]))
            continue
        bad = find_non_ascii_lines(text)
        if bad:
            failures.append((path, bad))

    if not failures:
        print("OK: PM markdown ASCII guard passed")
        return 0

    print("ERROR: PM ASCII guard failed")
    print("Non-ASCII detected in PM docs/tasks files (excluding .pm/inbox/raw/**):")
    for path, bad in failures:
        rel = path.relative_to(repo)
        print(f" - {rel}")
        for ln, chars, preview in bad[:5]:
            if ln == 0:
                print(f"    decode-error: {preview}")
            else:
                print(f"    line {ln}: chars={chars!r} preview={preview[:100]}")
        if len(bad) > 5:
            print(f"    ... {len(bad)-5} more lines")
    print("ACTION: replace smart punctuation with ASCII equivalents (e.g., — -> -, ’ -> ').")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
