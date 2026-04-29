#!/usr/bin/env python3
"""run_facet_checks.py

Execute facet-plan merged.checks validation with actionable diagnostics.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run merged.checks from facet-plan")
    p.add_argument("project", nargs="?", default=".", help="Project root")
    p.add_argument("--plan", default=".pm/generated/facet-plan.yml", help="Facet plan path relative to project")
    p.add_argument("--json", action="store_true", help="Emit JSON output")
    return p.parse_args()


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_check(project: Path, check: dict[str, Any]) -> tuple[bool, str, str]:
    cid = str(check.get("id", "")).strip() or "unnamed-check"
    ctype = str(check.get("type", "")).strip()

    if ctype == "file_exists":
        rel = str(check.get("path", "")).strip()
        if not rel:
            return False, cid, "missing required 'path' for file_exists"
        target = (project / rel).resolve()
        if target.exists():
            return True, cid, f"PASS file_exists: {rel}"
        return False, cid, f"missing required file: {rel}"

    if ctype == "contains_text":
        rel = str(check.get("path", "")).strip()
        expected = str(check.get("text", ""))
        if not rel:
            return False, cid, "missing required 'path' for contains_text"
        target = (project / rel).resolve()
        if not target.is_file():
            return False, cid, f"file not found for contains_text: {rel}"
        body = target.read_text(encoding="utf-8")
        if expected in body:
            return True, cid, f"PASS contains_text: {rel}"
        return False, cid, f"expected text not found in {rel}"

    return False, cid, f"unsupported check type: {ctype!r}"


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    plan_path = project / args.plan

    if not plan_path.is_file():
        out = {"ok": True, "checks": [], "note": "facet plan not found; skipping checks"}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print("INFO: facet plan not found; skipping checks")
        return 0

    raw = load_yaml(plan_path)
    merged = raw.get("merged") if isinstance(raw, dict) else None
    checks = merged.get("checks") if isinstance(merged, dict) else None

    if checks is None:
        out = {"ok": True, "checks": [], "note": "no merged.checks defined"}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print("INFO: no merged.checks defined")
        return 0

    if not isinstance(checks, list):
        msg = "merged.checks must be a list"
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, indent=2))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    results: list[dict[str, Any]] = []
    failed = False
    for item in checks:
        if not isinstance(item, dict):
            results.append({"ok": False, "id": "invalid", "message": "check entry must be object"})
            failed = True
            continue
        ok, cid, msg = run_check(project, item)
        if not ok:
            failed = True
        results.append({"ok": ok, "id": cid, "message": msg, "check": item})

    out = {"ok": not failed, "checks": results}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for r in results:
            level = "PASS" if r["ok"] else "FAIL"
            print(f"{level}: {r['id']}: {r['message']}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
