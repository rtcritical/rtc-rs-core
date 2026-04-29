#!/usr/bin/env python3
"""check_pm_runtime_brief.py

Validate PM runtime brief freshness + anti-hardcoded facet routing guard.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pm_runtime_brief_lib import build_runtime_brief, dump_runtime_brief_yaml


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check PM runtime brief integrity")
    p.add_argument("project", nargs="?", default=".", help="Project root")
    p.add_argument("--brief", default=".pm/generated/pm-runtime-brief.yml", help="Brief path relative to project")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    brief_path = project / args.brief

    if not brief_path.is_file():
        print(f"ERROR: runtime brief missing: {brief_path}")
        return 1

    expected = dump_runtime_brief_yaml(build_runtime_brief(project))
    current = brief_path.read_text(encoding="utf-8")
    if current != expected:
        print(f"ERROR: runtime brief drift detected: {brief_path}")
        print("Remediation: run python3 scripts/generate_pm_runtime_brief.py <project>")
        return 1

    pm_ops = project / ".pm" / "procedures" / "pm-operations.md"
    if pm_ops.is_file():
        body = pm_ops.read_text(encoding="utf-8")
        # Kernel should avoid hardcoding specific facet IDs in routing guidance.
        hits = re.findall(r"\bpm\.[a-z0-9-]+(?:\.[a-z0-9-]+)+\b", body)
        disallowed = sorted({h for h in hits if h not in {"pm-runtime-brief-v1"}})
        if disallowed:
            print(
                "ERROR: pm-operations contains hardcoded facet identifiers; "
                "use runtime brief references instead"
            )
            for h in disallowed:
                print(f"  - {h}")
            return 1

    print("OK: PM runtime brief guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
