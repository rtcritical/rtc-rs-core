#!/usr/bin/env python3
"""Enforce clean task-boundary git hygiene.

Default mode (pre-commit/task-boundary):
- allow staged changes
- fail on unstaged tracked changes
- fail on untracked files

Strict mode (--require-clean-index):
- also fail if staged changes exist
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_git(repo: Path, args: list[str]) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip() or f"git command failed: {' '.join(args)}")
    return p.stdout


def list_staged(repo: Path) -> list[str]:
    out = run_git(repo, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def list_unstaged_tracked(repo: Path) -> list[str]:
    out = run_git(repo, ["diff", "--name-only"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def list_untracked(repo: Path) -> list[str]:
    out = run_git(repo, ["ls-files", "--others", "--exclude-standard"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enforce clean git workspace at task boundaries")
    p.add_argument("repo", nargs="?", default=".", help="Repo root (default: .)")
    p.add_argument("--require-clean-index", action="store_true", help="Also require no staged changes")
    p.add_argument("--allow-untracked", action="store_true", help="Allow untracked files")
    p.add_argument(
        "--allow-path",
        action="append",
        default=[],
        help="Allow path prefix (repeatable) for staged/unstaged/untracked files",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()

    if not (repo / ".git").exists():
        print(f"ERROR: not a git repo: {repo}")
        return 2

    allowed_prefixes = [str(x).strip() for x in (args.allow_path or []) if str(x).strip()]

    def is_allowed(path: str) -> bool:
        return any(path == p or path.startswith(p.rstrip("/") + "/") for p in allowed_prefixes)

    staged = [p for p in list_staged(repo) if not is_allowed(p)]
    unstaged = [p for p in list_unstaged_tracked(repo) if not is_allowed(p)]
    untracked = [p for p in list_untracked(repo) if not is_allowed(p)]

    errors: list[str] = []

    if args.require_clean_index and staged:
        errors.append("staged changes present")

    if unstaged:
        errors.append("unstaged tracked changes present")

    if untracked and not args.allow_untracked:
        errors.append("untracked files present")

    if errors:
        print("ERROR: git task-boundary cleanliness check failed")
        for e in errors:
            print(f"  - {e}")
        if staged:
            print("  staged:")
            for p in staged:
                print(f"    - {p}")
        if unstaged:
            print("  unstaged:")
            for p in unstaged:
                print(f"    - {p}")
        if untracked and not args.allow_untracked:
            print("  untracked:")
            for p in untracked:
                print(f"    - {p}")
        print("Remediation: stage or revert all task-scope edits before committing.")
        return 1

    mode = "strict" if args.require_clean_index else "pre-commit"
    print(f"OK: git task-boundary cleanliness check passed ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
