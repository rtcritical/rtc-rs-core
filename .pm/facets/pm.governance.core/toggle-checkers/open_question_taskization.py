from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

GOVERNANCE_PATH_PATTERNS = (
    "docs/policy/",
    "docs/spec/",
    "templates/pm/",
    "skills/",
    "scripts/",
)

OQ_STATUS_ALLOWED = {"open", "approved", "rejected", "deferred"}
IMPLEMENTATION_PATH_PATTERNS = (
    "scripts/",
    "skills/",
    "templates/pm/",
    ".githooks/",
)


def _load_yaml_file(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_task_ids(repo: Path) -> set[str]:
    out: set[str] = set()
    tasks = repo / ".pm" / "tasks"
    if not tasks.is_dir() or yaml is None:
        return out
    for p in sorted(tasks.glob("T-*.yml")):
        try:
            data = _load_yaml_file(p)
        except Exception:
            continue
        if isinstance(data, dict):
            tid = str(data.get("task_id", "")).strip()
            if tid:
                out.add(tid)
    return out


def _valid_due_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()))


def _normalize_oq_status(q: dict[str, Any]) -> tuple[str, str | None]:
    status = str(q.get("status", "")).strip()
    decision = str(q.get("decision", "")).strip().lower()
    if status in OQ_STATUS_ALLOWED:
        return status, None
    if status == "decide-now":
        if decision == "accept":
            return "approved", "legacy status 'decide-now' mapped to 'approved'"
        return "open", "legacy status 'decide-now' mapped to 'open'"
    if status == "defer-with-owner-date":
        return "deferred", "legacy status 'defer-with-owner-date' mapped to 'deferred'"
    if status == "reject":
        return "rejected", "legacy status 'reject' mapped to 'rejected'"
    return "", None


def _is_staged(repo: Path, relpath: str) -> bool:
    import subprocess

    p = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-only", "--", relpath],
        capture_output=True,
        text=True,
    )
    return p.returncode == 0 and bool((p.stdout or "").strip())


def run(repo: Path, _toggle_cfg: dict[str, Any], staged: list[str]):
    errors: list[str] = []
    warnings: list[str] = []

    governance_touched = [
        p for p in staged if any(p.startswith(prefix) for prefix in GOVERNANCE_PATH_PATTERNS)
    ]
    details: dict[str, Any] = {
        "triggered": bool(governance_touched),
        "governance_paths": governance_touched,
        "artifact": ".pm/decisions/open-questions.yml",
        "source": "pm.governance.core.plugin",
    }

    if not governance_touched:
        return errors, warnings, details

    artifact_rel = ".pm/decisions/open-questions.yml"
    artifact = repo / artifact_rel
    if not artifact.is_file():
        errors.append(f"missing required planning artifact: {artifact_rel}")
        return errors, warnings, details

    if not _is_staged(repo, artifact_rel):
        errors.append(
            f"planning artifact must be staged with governance changes: {artifact_rel}"
        )

    if yaml is None:
        errors.append("PyYAML required for open-question taskization checker")
        return errors, warnings, details

    try:
        data = _load_yaml_file(artifact)
    except Exception as e:
        errors.append(f"open-questions artifact parse failure: {e}")
        return errors, warnings, details

    if not isinstance(data, dict):
        errors.append("open-questions artifact must be a YAML object")
        return errors, warnings, details

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("open-questions artifact must contain non-empty questions list")
        return errors, warnings, details

    task_ids = _load_task_ids(repo)
    open_questions: list[str] = []
    implementation_touched = [
        p for p in staged if any(p.startswith(prefix) for prefix in IMPLEMENTATION_PATH_PATTERNS)
    ]
    details["implementation_paths"] = implementation_touched

    for i, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            errors.append(f"questions[{i}] must be an object")
            continue

        status, legacy_note = _normalize_oq_status(q)
        if legacy_note:
            warnings.append(f"questions[{i}] {legacy_note}")

        if status not in OQ_STATUS_ALLOWED:
            errors.append(
                f"questions[{i}] status must be one of {sorted(OQ_STATUS_ALLOWED)}"
            )
            continue

        task_id = str(q.get("task_id", "")).strip()
        if status in {"open", "approved", "deferred"}:
            if not task_id:
                errors.append(f"questions[{i}] requires task_id for status={status}")
            elif task_id not in task_ids:
                errors.append(f"questions[{i}] task_id not found in .pm/tasks: {task_id}")

        resolved_by = str(q.get("resolved_by", "")).strip()
        resolved_at = str(q.get("resolved_at_utc", "")).strip()

        if status in {"approved", "rejected", "deferred"}:
            if not resolved_by:
                errors.append(f"questions[{i}] missing resolved_by for status={status}")
            if not resolved_at:
                errors.append(f"questions[{i}] missing resolved_at_utc for status={status}")

        if status == "open" and (resolved_by or resolved_at):
            errors.append(f"questions[{i}] open status may not include resolved_by/resolved_at_utc")

        if status == "deferred":
            owner = str(q.get("owner", "")).strip()
            due = str(q.get("due", "")).strip()
            if not owner:
                errors.append(f"questions[{i}] missing owner for deferred")
            if not due or not _valid_due_date(due):
                errors.append(
                    f"questions[{i}] missing/invalid due date (expected YYYY-MM-DD)"
                )

        qid = str(q.get("id", "")).strip() or f"questions[{i}]"
        if status == "open":
            open_questions.append(f"{qid} ({task_id or 'no-task'})")

    details["open_question_count"] = len(open_questions)
    if implementation_touched and open_questions:
        preview = ", ".join(open_questions[:6])
        errors.append(
            "implementation changes require prior OQ approval; resolve open questions first: "
            + preview
        )

    return errors, warnings, details
