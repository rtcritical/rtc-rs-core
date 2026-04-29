#!/usr/bin/env python3
"""check_pm_lane_compliance.py

What:
  Enforces PM default-lane closeout requirements on done backlog tasks.

Why:
  Prevent medium/high-risk tasks from being marked done without verifier evidence.

How:
  - Parses `.pm/backlog.md` task table rows
  - Detects done tasks tagged with risk tier in Notes
  - Requires verifier pass + verifier evidence markers for medium/high risk

Usage:
  python3 scripts/check_pm_lane_compliance.py <project-path>
  python3 scripts/check_pm_lane_compliance.py <project-path> --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

RISK_RE = re.compile(r"\brisk(?:_tier)?\s*[:=]\s*(low|medium|high)\b", re.IGNORECASE)
VERIFIER_PASS_RE = re.compile(r"\bverifier(?:_result)?\s*[:=]\s*(pass|passed|ok)\b", re.IGNORECASE)
VERIFIER_EVIDENCE_RE = re.compile(r"\bverifier(?:_evidence)?\s*[:=]\s*[^;|,]+", re.IGNORECASE)
EVIDENCE_RE = re.compile(r"\bevidence\s*[:=]\s*[^;|,]+", re.IGNORECASE)
EXC_APPROVER_RE = re.compile(r"\bpolicy_exception_approved_by\s*[:=]\s*[^;|,]+", re.IGNORECASE)
EXC_REASON_RE = re.compile(r"\bpolicy_exception_reason\s*[:=]\s*[^;|,]+", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check PM default-lane compliance markers in backlog done tasks")
    p.add_argument("target", nargs="?", default=".", help="Project root or backlog.md path")
    p.add_argument("--json", action="store_true", help="Emit JSON result payload")
    p.add_argument(
        "--fail-on-missing-risk-tag",
        action="store_true",
        help="Fail when done tasks have no risk tag in Notes (default: warn only)",
    )
    return p.parse_args()


def resolve_backlog(target: str) -> Path:
    p = Path(target).resolve()
    if p.is_file():
        return p
    return p / ".pm" / "backlog.md"


def split_cells(line: str) -> List[str]:
    raw = line.strip().strip("|")
    return [c.strip() for c in raw.split("|")]


def parse_task_table(backlog_text: str) -> Tuple[List[str], List[Dict[str, str]]]:
    lines = backlog_text.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "## task list":
            start_idx = i
            break
    if start_idx is None:
        return [], []

    table_lines: List[str] = []
    for line in lines[start_idx + 1 :]:
        if not line.strip():
            if table_lines:
                break
            continue
        if not line.lstrip().startswith("|"):
            if table_lines:
                break
            continue
        table_lines.append(line)

    if len(table_lines) < 2:
        return [], []

    headers = split_cells(table_lines[0])
    rows: List[Dict[str, str]] = []
    for line in table_lines[2:]:  # skip header + separator
        cells = split_cells(line)
        if not cells or all(not c for c in cells):
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = {headers[i]: cells[i] for i in range(len(headers))}
        rows.append(row)

    return headers, rows


def get_field(row: Dict[str, str], *names: str) -> str:
    normalized = {k.strip().lower(): v for k, v in row.items()}
    for n in names:
        if n.lower() in normalized:
            return normalized[n.lower()]
    return ""


def check_row(row: Dict[str, str]) -> Dict[str, object]:
    task_id = get_field(row, "Task ID", "Task", "ID") or "<unknown-task>"
    status = get_field(row, "Status").strip().lower()
    notes = get_field(row, "Notes")

    out: Dict[str, object] = {
        "task_id": task_id,
        "status": status,
        "risk": None,
        "compliant": True,
        "issues": [],
        "warnings": [],
    }

    if status != "done":
        return out

    risk_m = RISK_RE.search(notes)
    if not risk_m:
        out["warnings"] = ["done task missing risk tag in Notes"]
        return out

    risk = risk_m.group(1).lower()
    out["risk"] = risk

    if risk not in {"medium", "high"}:
        return out

    if EXC_APPROVER_RE.search(notes) and EXC_REASON_RE.search(notes):
        out["warnings"] = ["policy exception recorded; verifier gate bypass accepted"]
        return out

    has_verifier_pass = bool(VERIFIER_PASS_RE.search(notes))
    has_verifier_evidence = bool(VERIFIER_EVIDENCE_RE.search(notes) or EVIDENCE_RE.search(notes))

    issues: List[str] = []
    if not has_verifier_pass:
        issues.append("missing verifier pass marker (e.g., verifier_result=pass)")
    if not has_verifier_evidence:
        issues.append("missing verifier evidence marker (e.g., verifier_evidence=<artifact>)")

    if issues:
        out["compliant"] = False
        out["issues"] = issues

    return out


def main() -> int:
    args = parse_args()
    backlog = resolve_backlog(args.target)

    if not backlog.is_file():
        msg = f"ERROR: backlog file not found: {backlog}"
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, indent=2))
        else:
            print(msg)
        return 2

    text = backlog.read_text(encoding="utf-8")
    headers, rows = parse_task_table(text)

    if not headers:
        msg = "ERROR: could not parse '## Task List' markdown table"
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, indent=2))
        else:
            print(msg)
        return 2

    checks = [check_row(r) for r in rows]

    failures: List[str] = []
    warnings: List[str] = []

    for c in checks:
        task_id = str(c["task_id"])
        for w in c["warnings"]:  # type: ignore[index]
            warnings.append(f"{task_id}: {w}")
        if not c["compliant"]:
            issues = "; ".join(c["issues"])  # type: ignore[index]
            failures.append(f"{task_id}: {issues}")

    if args.fail_on_missing_risk_tag:
        for c in checks:
            if c["status"] == "done" and c["risk"] is None:
                failures.append(f"{c['task_id']}: done task missing risk tag in Notes")

    ok = len(failures) == 0

    if args.json:
        print(
            json.dumps(
                {
                    "ok": ok,
                    "backlog": str(backlog),
                    "checked_rows": len(rows),
                    "failures": failures,
                    "warnings": warnings,
                },
                indent=2,
            )
        )
    else:
        for w in warnings:
            print(f"WARN: {w}")
        for f in failures:
            print(f"ERROR: {f}")
        if ok:
            print(f"OK: PM lane compliance check passed ({len(rows)} task rows)")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
