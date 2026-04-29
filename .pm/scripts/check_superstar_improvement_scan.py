#!/usr/bin/env python3
"""Deterministic pre-commit superstar improvement scan + optional opt-in submission."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Idea:
    title: str
    impact: str
    rationale: str
    suggested_action: str


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else {}


def _dated_status_files(status_dir: Path) -> list[Path]:
    if not status_dir.exists():
        return []
    out: list[Path] = []
    for p in status_dir.glob("*.md"):
        stem = p.stem
        if len(stem) == 10:
            try:
                datetime.strptime(stem, "%Y-%m-%d")
                out.append(p)
            except ValueError:
                pass
    return sorted(out)


def _task_readiness_gaps(tasks_dir: Path) -> tuple[int, int]:
    total_open = 0
    not_ready = 0
    for p in sorted(tasks_dir.glob("T-*.yml")):
        d = _load_yaml(p)
        status = str(d.get("status", "")).strip().lower()
        if status in {"done", "abandoned", "superseded"}:
            continue
        total_open += 1
        required = ["scope_in", "scope_out", "acceptance_criteria", "required_evidence"]
        ready = True
        for k in required:
            v = d.get(k)
            if not isinstance(v, list) or len(v) == 0:
                ready = False
                break
        if not ready:
            not_ready += 1
    return total_open, not_ready


def _priority0_pending(tasks_dir: Path) -> int:
    n = 0
    for p in sorted(tasks_dir.glob("T-*.yml")):
        d = _load_yaml(p)
        status = str(d.get("status", "")).strip().lower()
        if status in {"done", "abandoned", "superseded"}:
            continue
        if str(d.get("priority", "")).strip().upper() == "P0":
            n += 1
    return n


def build_ideas(project: Path) -> list[Idea]:
    pm = project / ".pm"
    tasks_dir = pm / "tasks"
    status_dir = pm / "status"

    ideas: list[Idea] = []

    total_open, not_ready = _task_readiness_gaps(tasks_dir)
    if total_open > 0:
        pct = round((not_ready / total_open) * 100, 2)
        ideas.append(
            Idea(
                title="Raise execution readiness for open tasks",
                impact="high",
                rationale=f"{not_ready}/{total_open} open tasks are not execution-ready ({pct}%).",
                suggested_action="Harden top open tasks with scope_in/scope_out/acceptance_criteria/required_evidence before execution.",
            )
        )

    dated = _dated_status_files(status_dir)
    if dated:
        latest = datetime.strptime(dated[-1].stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        delta = (datetime.now(timezone.utc).date() - latest.date()).days
        if delta > 1:
            ideas.append(
                Idea(
                    title="Recover PM status freshness cadence",
                    impact="medium",
                    rationale=f"Latest dated status entry is {dated[-1].stem} ({delta} days stale).",
                    suggested_action="Publish/update today's .pm/status/YYYY-MM-DD.md with KPI snapshot and current blockers.",
                )
            )

    p0_open = _priority0_pending(tasks_dir)
    if p0_open > 0:
        ideas.append(
            Idea(
                title="Reduce concurrent P0 surface area",
                impact="high",
                rationale=f"There are {p0_open} non-terminal P0 tasks.",
                suggested_action="Sequence P0 tasks into one active slice at a time and taskize spillover as explicit dependencies.",
            )
        )

    ideas.append(
        Idea(
            title="Keep runtime-template PM parity green",
            impact="medium",
            rationale="Template drift recently caused baseline regressions (metrics/link parity).",
            suggested_action="Require check_pm_template_parity in commit path for baseline PM changes and add parity-focused E2E when introducing new artifacts.",
        )
    )

    return ideas


def write_submission(project: Path, selected: list[tuple[int, Idea]], output_note: Path | None = None) -> Path:
    inbox = project / ".pm" / "inbox" / "raw"
    inbox.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d-%H%M")
    path = output_note or (inbox / f"{ts}-superstar-improvement-scan-opt-in-submission.md")
    lines = [
        "# Intake Note",
        f"- captured_at: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "- source_type: system_scan",
        "- source_ref: scripts/check_superstar_improvement_scan.py",
        "- captured_by: pm-agent",
        "- submitted_to: PM admins (opt-in)",
        "",
        "## Raw Content",
        "User opted in to submit selected superstar improvement ideas.",
        "",
        "## Selected Ideas",
    ]
    for i, idea in selected:
        lines.extend(
            [
                f"### {i}. {idea.title}",
                f"- impact: {idea.impact}",
                f"- rationale: {idea.rationale}",
                f"- suggested_action: {idea.suggested_action}",
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def parse_submit(value: str, max_n: int) -> list[int]:
    v = value.strip().lower()
    if v == "all":
        return list(range(1, max_n + 1))
    picks: list[int] = []
    for tok in value.split(","):
        tok = tok.strip()
        if not tok:
            continue
        i = int(tok)
        if i < 1 or i > max_n:
            raise ValueError(f"idea index out of range: {i}")
        picks.append(i)
    if not picks:
        raise ValueError("no idea numbers provided")
    return sorted(set(picks))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run superstar improvement scan and optionally submit selected ideas")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--submit", help="Comma-delimited idea numbers or 'all' to opt-in submission")
    ap.add_argument("--output-note", help="Optional explicit output note path for submission")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    ideas = build_ideas(project)[: max(args.top, 1)]

    payload = {
        "ok": True,
        "project": str(project),
        "ideas": [
            {
                "id": i + 1,
                "title": idea.title,
                "impact": idea.impact,
                "rationale": idea.rationale,
                "suggested_action": idea.suggested_action,
            }
            for i, idea in enumerate(ideas)
        ],
        "opt_in_hint": "To submit selected ideas to PM admins, run: python3 scripts/check_superstar_improvement_scan.py <project> --submit 1,2 (or --submit all)",
    }

    submitted_path = None
    if args.submit:
        indexes = parse_submit(args.submit, len(ideas))
        selected = [(i, ideas[i - 1]) for i in indexes]
        note_path = Path(args.output_note).resolve() if args.output_note else None
        submitted_path = write_submission(project, selected, note_path)
        payload["submitted"] = {
            "selected_ids": indexes,
            "note": str(submitted_path),
        }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("SUPERSTAR IMPROVEMENT SCAN")
        if not ideas:
            print("- No ideas generated.")
        for i, idea in enumerate(ideas, start=1):
            print(f"{i}. [{idea.impact}] {idea.title}")
            print(f"   rationale: {idea.rationale}")
            print(f"   action: {idea.suggested_action}")
        print("")
        print(payload["opt_in_hint"])
        if submitted_path:
            print(f"OPT-IN SUBMISSION: wrote {submitted_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
