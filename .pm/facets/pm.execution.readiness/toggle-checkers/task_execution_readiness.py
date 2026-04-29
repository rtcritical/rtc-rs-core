from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

TASK_PATH_PREFIX = ".pm/tasks/"
TASK_FILE_PATTERN = "T-*.yml"

REQUIRED_FIELDS = [
    "objective",
    "scope",
    "constraints",
    "assumptions",
    "decision_rationale",
    "alternatives_considered",
    "dependencies",
    "acceptance_criteria",
    "validation_plan",
    "rollback_risk",
    "open_questions",
]

DISPLAY_NAME = {
    "objective": "objective",
    "scope": "scope",
    "constraints": "constraints",
    "assumptions": "assumptions",
    "decision_rationale": "decision rationale",
    "alternatives_considered": "alternatives considered",
    "dependencies": "dependencies",
    "acceptance_criteria": "acceptance criteria",
    "validation_plan": "validation plan",
    "rollback_risk": "rollback/risk",
    "open_questions": "open questions",
}

IMPLEMENTATION_PATHS = (
    "scripts/",
    "skills/",
    "templates/pm/",
    ".githooks/",
    "docs/",
)


def _load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _missing_readiness_fields(exec_block: Any) -> list[str]:
    if not isinstance(exec_block, dict):
        return [DISPLAY_NAME[k] for k in REQUIRED_FIELDS]
    missing: list[str] = []
    for key in REQUIRED_FIELDS:
        if not _non_empty(exec_block.get(key)):
            missing.append(DISPLAY_NAME[key])
    return missing


def _candidate_tasks(staged: list[str], repo: Path) -> list[str]:
    staged_task_files = [p for p in staged if p.startswith(TASK_PATH_PREFIX)]
    if staged_task_files:
        return sorted(set(staged_task_files))

    impl_touched = any(any(p.startswith(prefix) for prefix in IMPLEMENTATION_PATHS) for p in staged)
    if not impl_touched:
        return []

    tasks_dir = repo / ".pm" / "tasks"
    if not tasks_dir.is_dir():
        return []
    return sorted(str(p.relative_to(repo)) for p in tasks_dir.glob(TASK_FILE_PATTERN))


def run(repo: Path, _toggle_cfg: dict[str, Any], staged: list[str]):
    errors: list[str] = []
    warnings: list[str] = []

    target_tasks = _candidate_tasks(staged, repo)
    details: dict[str, Any] = {
        "triggered": bool(target_tasks),
        "required_fields": [DISPLAY_NAME[k] for k in REQUIRED_FIELDS],
        "checked_tasks": target_tasks,
        "source": "pm.execution.readiness.plugin",
    }

    if not target_tasks:
        return errors, warnings, details

    if yaml is None:
        errors.append("PyYAML required for task execution readiness checker")
        return errors, warnings, details

    per_task_missing: dict[str, list[str]] = {}

    for rel in target_tasks:
        task_path = repo / rel
        if not task_path.is_file():
            errors.append(f"missing task file referenced for readiness check: {rel}")
            continue

        try:
            task_doc = _load_yaml(task_path)
        except Exception as e:
            errors.append(f"task parse failure for {rel}: {e}")
            continue

        if not isinstance(task_doc, dict):
            errors.append(f"task file must be a YAML object: {rel}")
            continue

        readiness = task_doc.get("execution_readiness")
        missing = _missing_readiness_fields(readiness)
        if missing:
            per_task_missing[rel] = missing
            errors.append(
                f"execution readiness incomplete for {rel}; missing fields: {', '.join(missing)}"
            )

    details["missing_by_task"] = per_task_missing

    if per_task_missing:
        errors.append(
            "remediation: populate .pm/tasks/<task>.yml.execution_readiness with all required fields "
            "(objective, scope, constraints, assumptions, decision rationale, alternatives considered, "
            "dependencies, acceptance criteria, validation plan, rollback/risk, open questions)"
        )

    return errors, warnings, details
