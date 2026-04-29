#!/usr/bin/env python3
"""generate_pm_runtime_brief.py

Generate deterministic .pm/generated/pm-runtime-brief.yml from active facets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pm_runtime_brief_lib import build_runtime_brief, dump_runtime_brief_yaml


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate PM runtime brief from active facets")
    p.add_argument("project", nargs="?", default=".", help="Project root")
    p.add_argument("--out", default=".pm/generated/pm-runtime-brief.yml", help="Output path relative to project")
    p.add_argument("--check", action="store_true", help="Fail if generated output differs from on-disk file")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    out_path = project / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    brief = build_runtime_brief(project)
    content = dump_runtime_brief_yaml(brief)

    if args.check:
        if not out_path.is_file():
            print(f"ERROR: runtime brief missing: {out_path}")
            return 1
        current = out_path.read_text(encoding="utf-8")
        if current != content:
            print(f"ERROR: runtime brief drift detected: {out_path}")
            return 1
        print(f"OK: runtime brief up-to-date: {out_path}")
        return 0

    out_path.write_text(content, encoding="utf-8")
    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
