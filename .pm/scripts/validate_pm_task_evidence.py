#!/usr/bin/env python3
"""validate_pm_task_evidence.py

Hard gate: for terminal PM tasks, ensure evidence refs and intake refs are git-tracked
(or staged in index) and present on disk.

If any check fails, exit non-zero with actionable diagnostics.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

TERMINAL = {"done", "abandoned", "superseded"}


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def is_tracked_or_staged(repo: Path, rel: str) -> bool:
    # tracked in HEAD/index/worktree
    rc, _, _ = run_git(repo, ["ls-files", "--", rel])
    if rc == 0:
        rc2, out, _ = run_git(repo, ["ls-files", "--", rel])
        if out.strip():
            return True
    # staged but newly added
    rc, out, _ = run_git(repo, ["diff", "--cached", "--name-only", "--", rel])
    return rc == 0 and bool(out.strip())


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_task(repo: Path, task_path: Path) -> list[str]:
    errors: list[str] = []
    data = load_yaml(task_path)
    if not isinstance(data, dict):
        return [f"{task_path}: invalid YAML object"]

    status = str(data.get("status", "")).strip()
    if status not in TERMINAL:
        return []

    refs: list[str] = []
    for field in ["intake_refs", "evidence_refs", "completion_evidence"]:
        val = data.get(field, [])
        if isinstance(val, list):
            refs.extend(str(x).strip() for x in val if str(x).strip())

    # De-dup while preserving order
    seen = set()
    deduped = []
    for r in refs:
        if r not in seen:
            deduped.append(r)
            seen.add(r)

    for rel in deduped:
        # anchor-style refs are allowed; verify file portion only
        file_part = rel.split("#", 1)[0]
        if not file_part:
            continue
        p = repo / file_part
        if not p.exists():
            errors.append(f"{task_path.name}: ref missing on disk -> {rel}")
            continue
        if not is_tracked_or_staged(repo, file_part):
            errors.append(f"{task_path.name}: ref not tracked/staged in git -> {rel}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate terminal PM task refs are tracked/staged in git")
    parser.add_argument("repo", nargs="?", default=".", help="Repo root path")
    args = parser.parse_args()

    if yaml is None:
        print("ERROR: PyYAML required", file=sys.stderr)
        return 2

    repo = Path(args.repo).resolve()
    tasks_dir = repo / ".pm" / "tasks"
    if not tasks_dir.is_dir():
        print("OK: no .pm/tasks directory")
        return 0

    all_errors: list[str] = []
    for task in sorted(tasks_dir.glob("T-*.yml")):
        all_errors.extend(check_task(repo, task))

    if all_errors:
        print("ERROR: PM task evidence tracking gate failed:")
        for e in all_errors:
            print(f" - {e}")
        print("ACTION: stage/add missing evidence refs or update task refs before commit.")
        return 1

    print("OK: PM task evidence refs are tracked/staged for terminal tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
