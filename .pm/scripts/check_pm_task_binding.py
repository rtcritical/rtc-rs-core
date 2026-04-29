#!/usr/bin/env python3
"""Enforce PM task-binding for implementation commits.

Rule:
- If staged changes include implementation-affecting paths, require at least one
  staged .pm/tasks/T-*.yml file in the same commit.

Implementation paths:
- scripts/
- test-scripts/
- skills/
- templates/pm/
- .githooks/
- docs/
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

TASK_FILE_RE = re.compile(r"^\.pm/tasks/T-\d+\.yml$")

IMPL_PREFIXES = (
    "scripts/",
    "test-scripts/",
    "skills/",
    "templates/pm/",
    ".githooks/",
    "docs/",
)


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip() or f"git failed: {' '.join(args)}")
    return p.stdout


def staged_files(repo: Path) -> list[str]:
    out = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [x.strip() for x in out.splitlines() if x.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Require staged PM task file when implementation paths are staged")
    p.add_argument("repo", nargs="?", default=".", help="Repo root")
    p.add_argument(
        "--impl-prefix",
        action="append",
        default=[],
        help="Additional implementation path prefix (repeatable)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: not a git repo: {repo}")
        return 2

    files = staged_files(repo)
    prefixes = IMPL_PREFIXES + tuple(str(x).strip() for x in args.impl_prefix if str(x).strip())

    impl_changed = [f for f in files if f.startswith(prefixes)]
    if not impl_changed:
        print("OK: task-binding guard skipped (no implementation paths staged)")
        return 0

    staged_task_files = [f for f in files if TASK_FILE_RE.fullmatch(f)]
    if not staged_task_files:
        print("ERROR: PM task-binding guard failed")
        print("  - implementation paths are staged but no .pm/tasks/T-*.yml file is staged")
        print("  implementation files:")
        for f in impl_changed:
            print(f"    - {f}")
        print("Remediation: stage at least one task file update in .pm/tasks/T-*.yml in the same commit.")
        return 1

    print("OK: PM task-binding guard passed")
    print("  staged task files:")
    for f in staged_task_files:
        print(f"    - {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
