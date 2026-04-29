#!/usr/bin/env python3
"""render_pm_task_views.py

What:
  Renders `.pm/backlog.md` and `.pm/closed.md` from canonical `.pm/tasks/*.yml`.

Why:
  Keep human-readable checked-in views in sync with canonical task files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


OPEN_STATES = {"todo", "in_progress", "blocked"}
CLOSED_STATES = {"done", "abandoned", "superseded"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render PM backlog/closed views from canonical task files")
    p.add_argument("target", nargs="?", default=".", help="Project root")
    p.add_argument("--check", action="store_true", help="Fail if generated content differs")
    p.add_argument("--json", action="store_true", help="Emit JSON output")
    return p.parse_args()


def load_tasks(tasks_dir: Path) -> list[dict]:
    out = []
    for p in sorted(tasks_dir.glob("T-*.yml")):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            out.append(data)
    return out


def owner_text(task: dict) -> str:
    o = task.get("owner") or {}
    if isinstance(o, dict):
        return str(o.get("id") or "n/a")
    return str(o)


def deps_text(task: dict) -> str:
    d = task.get("depends_on")
    if not d:
        return "-"
    if isinstance(d, list):
        return ",".join(str(x) for x in d)
    return str(d)


def notes_text(task: dict) -> str:
    refs = []
    for r in task.get("intake_refs") or []:
        refs.append(f"source_note={r}")
    for r in task.get("decision_refs") or []:
        refs.append(f"decision_ref={r}")
    for r in task.get("evidence_refs") or []:
        refs.append(f"evidence_ref={r}")
    risk = task.get("risk_tier")
    if risk:
        refs.append(f"risk={risk}")
    verifier_result = str(task.get("verifier_result", "")).strip()
    if verifier_result:
        refs.append(f"verifier_result={verifier_result}")
    verifier_evidence = task.get("verifier_evidence")
    if isinstance(verifier_evidence, list):
        for r in verifier_evidence:
            if str(r).strip():
                refs.append(f"verifier_evidence={r}")
    elif str(verifier_evidence or "").strip():
        refs.append(f"verifier_evidence={verifier_evidence}")
    n = task.get("notes") or []
    if isinstance(n, list):
        refs.extend(str(x) for x in n if str(x).strip())
    return "; ".join(refs) if refs else "-"


def status_for_backlog(task: dict) -> str:
    s = str(task.get("status") or "todo")
    return "in-progress" if s == "in_progress" else s


def render_table(tasks: list[dict], include_closed: bool) -> str:
    header = [
        "| Task ID | Epic ID | Task | Priority | Status | Owner | Depends On | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    rows = []
    for t in tasks:
        status = str(t.get("status") or "todo")
        if include_closed and status not in CLOSED_STATES:
            continue
        if not include_closed and status not in OPEN_STATES:
            continue
        rows.append(
            "| {tid} | {eid} | {task} | {pri} | {status} | {owner} | {deps} | {notes} |".format(
                tid=t.get("task_id", ""),
                eid=t.get("epic_id", ""),
                task=str(t.get("title", "")).replace("|", "\\|"),
                pri=t.get("priority", "P1"),
                status=(status_for_backlog(t) if not include_closed else status),
                owner=owner_text(t),
                deps=deps_text(t),
                notes=notes_text(t).replace("|", "\\|"),
            )
        )
    return "\n".join(header + rows) + "\n"


def render_backlog(tasks: list[dict], old_epic_block: str) -> str:
    open_tasks = [t for t in tasks if str(t.get("status")) in OPEN_STATES]
    open_tasks.sort(key=lambda t: (PRIORITY_ORDER.get(str(t.get("priority", "P2")), 9), str(t.get("updated_at", "")), str(t.get("task_id", ""))), reverse=False)

    out = ["# Backlog", "", "## Epic Mapping", "", old_epic_block.strip(), "", "## Task List", "", render_table(open_tasks, include_closed=False), "## Status Vocabulary", "", "- `todo`", "- `in-progress`", "- `blocked`", "- `done`", ""]
    return "\n".join(out)


def render_closed(tasks: list[dict]) -> str:
    closed = [t for t in tasks if str(t.get("status")) in CLOSED_STATES]
    closed.sort(key=lambda t: (str(t.get("closed_at", "")), str(t.get("task_id", ""))), reverse=True)
    out = ["# Closed Tasks", "", "Most recent closed tasks first.", "", "## Task List", "", render_table(closed, include_closed=True)]
    return "\n".join(out)


def epic_block_from_backlog(backlog_text: str) -> str:
    lines = backlog_text.splitlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "## epic mapping":
            start = i + 1
        elif start is not None and line.strip().lower() == "## task list":
            end = i
            break
    if start is None:
        return "| Epic ID | Goal Ref | Epic Name | Priority | Owner | Status | Completion Criteria |\n|---|---|---|---|---|---|---|"
    if end is None:
        end = len(lines)
    return "\n".join(lines[start:end]).strip() or "| Epic ID | Goal Ref | Epic Name | Priority | Owner | Status | Completion Criteria |\n|---|---|---|---|---|---|---|"


def main() -> int:
    args = parse_args()
    root = Path(args.target).resolve()
    pm = root / ".pm"
    tasks_dir = pm / "tasks"
    backlog_path = pm / "backlog.md"
    closed_path = pm / "closed.md"

    if not tasks_dir.is_dir():
        payload = {"ok": False, "error": f"tasks dir not found: {tasks_dir}"}
        print(json.dumps(payload, indent=2) if args.json else payload["error"])
        return 2

    old_backlog = backlog_path.read_text(encoding="utf-8") if backlog_path.exists() else ""
    tasks = load_tasks(tasks_dir)
    epic_block = epic_block_from_backlog(old_backlog)

    new_backlog = render_backlog(tasks, epic_block)
    new_closed = render_closed(tasks)

    backlog_changed = (old_backlog != new_backlog)
    old_closed = closed_path.read_text(encoding="utf-8") if closed_path.exists() else ""
    closed_changed = (old_closed != new_closed)

    if args.check:
        ok = not backlog_changed and not closed_changed
        payload = {
            "ok": ok,
            "backlog_changed": backlog_changed,
            "closed_changed": closed_changed,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("OK" if ok else "DRIFT")
        return 0 if ok else 1

    backlog_path.write_text(new_backlog, encoding="utf-8")
    closed_path.write_text(new_closed, encoding="utf-8")

    payload = {
        "ok": True,
        "tasks": len(tasks),
        "wrote_backlog": str(backlog_path),
        "wrote_closed": str(closed_path),
        "backlog_changed": backlog_changed,
        "closed_changed": closed_changed,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"OK: rendered tasks={len(tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
