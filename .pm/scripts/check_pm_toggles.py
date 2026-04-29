#!/usr/bin/env python3
"""check_pm_toggles.py

What:
  Enforces configurable PM runtime toggles through a checker registry.

Why:
  Keep policy/config toggle intent synchronized with actual runtime enforcement.

How:
  - Loads strict-authority mode + execution preset/overrides from .pm/project.yml
  - Resolves enabled toggles via a checker registry manifest (with safe defaults)
  - Runs checker handlers against staged changes and PM artifacts

Usage:
  python3 scripts/check_pm_toggles.py <project-path>
  python3 scripts/check_pm_toggles.py <project-path> --json
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

PRESET_DEFAULTS: dict[str, dict[str, bool]] = {
    "prototype": {
        "require_open_question_taskization": False,
        "require_task_execution_readiness": False,
    },
    "balanced": {
        "require_open_question_taskization": False,
        "require_task_execution_readiness": False,
    },
    "hardened": {
        "require_open_question_taskization": True,
        "require_task_execution_readiness": True,
    },
}

DEFAULT_REGISTRY: dict[str, Any] = {
    "schema_version": 1,
    "trusted_plugin_roots": [".pm/toggle-checkers", ".pm/facets"],
    "plugins": {},
    "toggles": {
        "require_open_question_taskization": {
            "checker": "open_question_taskization",
            "description": "Require a planning checkpoint artifact + taskized open questions for governance-impacting changes.",
        },
        "require_task_execution_readiness": {
            "checker": "task_execution_readiness",
            "description": "Require execution-ready engineering detail fields on impacted PM tasks before implementation.",
        }
    },
}

GOVERNANCE_PATH_PATTERNS = (
    "docs/policy/",
    "docs/spec/",
    "templates/pm/",
    "skills/",
    "scripts/",
)

OQ_STATUS_ALLOWED = {"open", "approved", "rejected", "deferred"}
LEGACY_STATUS_ALLOWED = {"decide-now", "defer-with-owner-date", "reject"}
IMPLEMENTATION_PATH_PATTERNS = (
    "scripts/",
    "skills/",
    "templates/pm/",
    ".githooks/",
)

READINESS_REQUIRED_FIELDS = [
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

READINESS_DISPLAY_FIELDS = {
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


CheckerFn = Callable[[Path, dict[str, Any], list[str]], tuple[list[str], list[str], dict[str, Any]]]


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def staged_files(repo: Path) -> list[str]:
    rc, out, _ = run_git(repo, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if rc != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_staged(repo: Path, relpath: str) -> bool:
    rc, out, _ = run_git(repo, ["diff", "--cached", "--name-only", "--", relpath])
    return rc == 0 and bool(out.strip())


def load_yaml_file(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_project_cfg(repo: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    cfg_path = repo / ".pm" / "project.yml"
    if not cfg_path.is_file():
        return {}, [".pm/project.yml missing"], warnings
    try:
        data = load_yaml_file(cfg_path)
    except Exception as e:
        return {}, [f"project.yml parse failure: {e}"], warnings
    if not isinstance(data, dict):
        return {}, ["project.yml must be a YAML object"], warnings
    return data, errors, warnings


def resolve_effective_toggles(project_cfg: dict[str, Any]) -> tuple[dict[str, bool], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    strict = project_cfg.get("strict_authority_mode")
    if strict is None:
        return {}, errors, ["strict_authority_mode not configured; toggle checks skipped"]
    if not isinstance(strict, dict):
        return {}, ["strict_authority_mode must be an object when present"], warnings

    if not bool(strict.get("enabled", False)):
        return {}, errors, ["strict_authority_mode.enabled=false; toggle checks skipped"]

    execution = strict.get("execution_mode", {})
    if execution is None:
        execution = {}
    if not isinstance(execution, dict):
        return {}, ["strict_authority_mode.execution_mode must be an object"], warnings

    preset = str(execution.get("preset", "balanced") or "balanced").strip().lower()
    if preset not in PRESET_DEFAULTS:
        errors.append(f"unknown execution_mode preset: {preset!r}")
        preset = "balanced"

    effective: dict[str, bool] = dict(PRESET_DEFAULTS.get(preset, {}))

    overrides = execution.get("overrides", {})
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        errors.append("strict_authority_mode.execution_mode.overrides must be an object")
    else:
        for k, v in overrides.items():
            if not isinstance(v, bool):
                errors.append(f"execution_mode.overrides.{k} must be boolean")
                continue
            effective[str(k)] = v

    toggles_block = strict.get("toggles", {})
    if toggles_block is None:
        toggles_block = {}
    if isinstance(toggles_block, dict):
        for k, v in toggles_block.items():
            if not isinstance(v, bool):
                errors.append(f"strict_authority_mode.toggles.{k} must be boolean")
                continue
            effective[str(k)] = v

    return effective, errors, warnings


def load_registry_layer(path: Path, layer_name: str) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {}, errors, [f"toggle registry layer not found: {layer_name}"]
    try:
        data = load_yaml_file(path)
    except Exception as e:
        return {}, [f"toggle registry parse failure in {layer_name}: {e}"], warnings
    if not isinstance(data, dict):
        return {}, [f"toggle registry layer must be YAML object: {layer_name}"], warnings
    if int(data.get("schema_version", 0) or 0) != 1:
        errors.append(f"toggle registry schema_version must be 1 ({layer_name})")

    trusted_roots = data.get("trusted_plugin_roots", [])
    if trusted_roots is None:
        trusted_roots = []
    if not isinstance(trusted_roots, list) or any(not isinstance(x, str) for x in trusted_roots):
        errors.append(f"toggle registry trusted_plugin_roots must be a list of strings ({layer_name})")

    plugins = data.get("plugins", {})
    if plugins is None:
        plugins = {}
    if not isinstance(plugins, dict):
        errors.append(f"toggle registry plugins must be an object ({layer_name})")
    else:
        for checker_id, plugin_cfg in plugins.items():
            if not isinstance(plugin_cfg, dict):
                errors.append(f"toggle registry plugins.{checker_id} must be an object ({layer_name})")
                continue
            path_v = plugin_cfg.get("path")
            if not isinstance(path_v, str) or not path_v.strip():
                errors.append(f"toggle registry plugins.{checker_id}.path must be non-empty string ({layer_name})")
            fn_v = plugin_cfg.get("function", "run")
            if not isinstance(fn_v, str) or not fn_v.strip():
                errors.append(f"toggle registry plugins.{checker_id}.function must be non-empty string when set ({layer_name})")

    toggles = data.get("toggles")
    if not isinstance(toggles, dict):
        errors.append(f"toggle registry toggles must be an object ({layer_name})")
    return data, errors, warnings


def _canonical(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"))


def _plugin_equiv(a: Any, b: Any) -> bool:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return _canonical(a) == _canonical(b)
    return (
        str(a.get("path", "")).strip() == str(b.get("path", "")).strip()
        and str(a.get("function", "run")).strip() == str(b.get("function", "run")).strip()
    )


def _toggle_equiv(a: Any, b: Any) -> bool:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return _canonical(a) == _canonical(b)
    return str(a.get("checker", "")).strip() == str(b.get("checker", "")).strip()


def _discover_facet_registry_layers(repo: Path, project_cfg: dict[str, Any]) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    active = project_cfg.get("active_facets", [])
    if not isinstance(active, list):
        return out
    for item in active:
        facet_id = str(item).strip()
        if not facet_id:
            continue
        p1 = repo / ".pm" / "facets" / facet_id / "config" / "toggle_registry.patch.yml"
        p2 = repo / ".pm" / "facets" / facet_id / "toggle_registry.patch.yml"
        if p1.is_file():
            out.append((f"facet:{facet_id}", p1))
        elif p2.is_file():
            out.append((f"facet:{facet_id}", p2))
    return out


def load_registry(repo: Path, project_cfg: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    effective: dict[str, Any] = copy.deepcopy(DEFAULT_REGISTRY)
    effective.setdefault("trusted_plugin_roots", [])
    effective.setdefault("plugins", {})
    effective.setdefault("toggles", {})

    project_registry_path = repo / ".pm" / "config" / "toggle_registry.yml"
    project_layer: dict[str, Any] = {}
    project_plugins: dict[str, Any] = {}
    project_toggles: dict[str, Any] = {}
    override_plugins: set[str] = set()
    override_toggles: set[str] = set()

    if project_registry_path.is_file():
        project_layer, p_err, p_warn = load_registry_layer(project_registry_path, "project")
        errors.extend(p_err)
        warnings.extend(p_warn)
        if isinstance(project_layer.get("plugins"), dict):
            project_plugins = project_layer.get("plugins", {})  # type: ignore[assignment]
        if isinstance(project_layer.get("toggles"), dict):
            project_toggles = project_layer.get("toggles", {})  # type: ignore[assignment]
        overrides = project_layer.get("overrides", {})
        if isinstance(overrides, dict):
            ps = overrides.get("plugins", [])
            ts = overrides.get("toggles", [])
            if isinstance(ps, list):
                override_plugins = {str(x).strip() for x in ps if str(x).strip()}
            if isinstance(ts, list):
                override_toggles = {str(x).strip() for x in ts if str(x).strip()}
    else:
        warnings.append("project toggle registry not found; using built-in defaults/facets only")

    facet_layers = _discover_facet_registry_layers(repo, project_cfg)

    def merge_layer(layer_name: str, layer: dict[str, Any], is_project: bool) -> None:
        roots = layer.get("trusted_plugin_roots", [])
        if isinstance(roots, list):
            for r in roots:
                rs = str(r).strip()
                if rs and rs not in effective["trusted_plugin_roots"]:
                    effective["trusted_plugin_roots"].append(rs)

        layer_plugins = layer.get("plugins", {})
        if isinstance(layer_plugins, dict):
            for checker_id, cfg in layer_plugins.items():
                k = str(checker_id).strip()
                if not k:
                    continue
                if k not in effective["plugins"]:
                    effective["plugins"][k] = cfg
                    continue
                if _plugin_equiv(effective["plugins"][k], cfg):
                    continue

                if is_project and k in override_plugins:
                    effective["plugins"][k] = cfg
                    continue

                if (not is_project) and (k in override_plugins) and (k in project_plugins):
                    continue

                errors.append(
                    f"toggle registry plugin conflict for {k!r} at {layer_name}; add project overrides.plugins entry + project mapping to override"
                )

        layer_toggles = layer.get("toggles", {})
        if isinstance(layer_toggles, dict):
            for toggle_name, cfg in layer_toggles.items():
                k = str(toggle_name).strip()
                if not k:
                    continue
                if k not in effective["toggles"]:
                    effective["toggles"][k] = cfg
                    continue
                if _toggle_equiv(effective["toggles"][k], cfg):
                    continue

                if is_project and k in override_toggles:
                    effective["toggles"][k] = cfg
                    continue

                if (not is_project) and (k in override_toggles) and (k in project_toggles):
                    continue

                errors.append(
                    f"toggle registry toggle conflict for {k!r} at {layer_name}; add project overrides.toggles entry + project mapping to override"
                )

    for layer_name, layer_path in facet_layers:
        layer_data, l_err, l_warn = load_registry_layer(layer_path, layer_name)
        errors.extend(l_err)
        warnings.extend(l_warn)
        merge_layer(layer_name, layer_data, False)

    if project_layer:
        merge_layer("project", project_layer, True)

    return effective, errors, warnings


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _trusted_plugin_roots(repo: Path, registry: dict[str, Any]) -> list[Path]:
    configured = registry.get("trusted_plugin_roots", []) if isinstance(registry, dict) else []
    roots: list[Path] = []
    if isinstance(configured, list):
        for item in configured:
            if isinstance(item, str) and item.strip():
                roots.append((repo / item).resolve())
    if not roots:
        roots = [(repo / ".pm/toggle-checkers").resolve(), (repo / ".pm/facets").resolve()]
    return roots


@lru_cache(maxsize=128)
def _load_plugin_function(plugin_abs_path: str, function_name: str) -> CheckerFn:
    p = Path(plugin_abs_path)
    module_name = f"pm_toggle_plugin_{abs(hash((plugin_abs_path, function_name)))}"
    spec = importlib.util.spec_from_file_location(module_name, str(p))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load plugin module spec from {p}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    fn = getattr(module, function_name, None)
    if not callable(fn):
        raise RuntimeError(f"plugin function not callable: {function_name} in {p}")
    return fn  # type: ignore[return-value]


def resolve_checker(
    repo: Path,
    checker_id: str,
    builtins: dict[str, CheckerFn],
    registry: dict[str, Any],
) -> tuple[CheckerFn | None, str | None, str | None, bool]:
    plugins = registry.get("plugins", {}) if isinstance(registry, dict) else {}
    if isinstance(plugins, dict) and isinstance(plugins.get(checker_id), dict):
        plugin_cfg = plugins.get(checker_id)

        rel_path = str(plugin_cfg.get("path", "")).strip()  # type: ignore[union-attr]
        fn_name = str(plugin_cfg.get("function", "run")).strip() or "run"  # type: ignore[union-attr]
        if rel_path:
            plugin_path = (repo / rel_path).resolve()
            trusted_roots = _trusted_plugin_roots(repo, registry)
            if any(_is_relative_to(plugin_path, root) for root in trusted_roots):
                if plugin_path.is_file():
                    try:
                        fn = _load_plugin_function(str(plugin_path), fn_name)
                        return fn, None, None, False
                    except Exception as e:
                        if checker_id in builtins:
                            return builtins[checker_id], None, f"plugin load failed; fell back to builtin for {checker_id!r}: {e}", True
                        return None, f"plugin checker load failed for {checker_id!r}: {e}", None, False
                else:
                    if checker_id in builtins:
                        return builtins[checker_id], None, f"plugin file missing; fell back to builtin for {checker_id!r}: {rel_path}", True
                    return None, f"plugin checker file missing: {rel_path}", None, False
            else:
                roots_txt = ", ".join(str(repo_path.relative_to(repo)) if _is_relative_to(repo_path, repo) else str(repo_path) for repo_path in trusted_roots)
                if checker_id in builtins:
                    return builtins[checker_id], None, f"plugin path outside trusted roots; fell back to builtin for {checker_id!r}: {rel_path}", True
                return None, f"plugin checker path not under trusted roots ({roots_txt}): {rel_path}", None, False
        if checker_id in builtins:
            return builtins[checker_id], None, f"plugin path missing; fell back to builtin for {checker_id!r}", True
        return None, f"plugin checker {checker_id!r} missing path", None, False

    if checker_id in builtins:
        return builtins[checker_id], None, None, False

    return None, f"enabled toggle references unknown checker: {checker_id!r}", None, False


def fail_on_builtin_fallback(project_cfg: dict[str, Any]) -> bool:
    strict = project_cfg.get("strict_authority_mode")
    if not isinstance(strict, dict):
        return False
    req = strict.get("plugin_requirements")
    if not isinstance(req, dict):
        return False
    return bool(req.get("fail_on_builtin_fallback", False))


def _load_task_ids(repo: Path) -> set[str]:
    out: set[str] = set()
    tasks = repo / ".pm" / "tasks"
    if not tasks.is_dir() or yaml is None:
        return out
    for p in sorted(tasks.glob("T-*.yml")):
        try:
            data = load_yaml_file(p)
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


def check_open_question_taskization(repo: Path, _toggle_cfg: dict[str, Any], staged: list[str]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    governance_touched = [
        p for p in staged if any(p.startswith(prefix) for prefix in GOVERNANCE_PATH_PATTERNS)
    ]
    details: dict[str, Any] = {
        "triggered": bool(governance_touched),
        "governance_paths": governance_touched,
        "artifact": ".pm/decisions/open-questions.yml",
    }

    if not governance_touched:
        return errors, warnings, details

    artifact_rel = ".pm/decisions/open-questions.yml"
    artifact = repo / artifact_rel
    if not artifact.is_file():
        errors.append(f"missing required planning artifact: {artifact_rel}")
        return errors, warnings, details

    if not is_staged(repo, artifact_rel):
        errors.append(
            f"planning artifact must be staged with governance changes: {artifact_rel}"
        )

    if yaml is None:
        errors.append("PyYAML required for open-question taskization checker")
        return errors, warnings, details

    try:
        data = load_yaml_file(artifact)
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


def _readiness_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _missing_readiness_fields(exec_block: Any) -> list[str]:
    if not isinstance(exec_block, dict):
        return [READINESS_DISPLAY_FIELDS[k] for k in READINESS_REQUIRED_FIELDS]
    out: list[str] = []
    for key in READINESS_REQUIRED_FIELDS:
        if not _readiness_non_empty(exec_block.get(key)):
            out.append(READINESS_DISPLAY_FIELDS[key])
    return out


def _candidate_tasks_for_readiness(repo: Path, staged: list[str]) -> list[str]:
    staged_task_files = [p for p in staged if p.startswith(".pm/tasks/")]
    if staged_task_files:
        return sorted(set(staged_task_files))

    implementation_touched = [
        p for p in staged if any(p.startswith(prefix) for prefix in IMPLEMENTATION_PATH_PATTERNS)
    ]
    if not implementation_touched:
        return []

    tasks_dir = repo / ".pm" / "tasks"
    if not tasks_dir.is_dir():
        return []
    return sorted(str(p.relative_to(repo)) for p in tasks_dir.glob("T-*.yml"))


def check_task_execution_readiness(repo: Path, _toggle_cfg: dict[str, Any], staged: list[str]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    target_tasks = _candidate_tasks_for_readiness(repo, staged)
    details: dict[str, Any] = {
        "triggered": bool(target_tasks),
        "required_fields": [READINESS_DISPLAY_FIELDS[k] for k in READINESS_REQUIRED_FIELDS],
        "checked_tasks": target_tasks,
    }

    if not target_tasks:
        return errors, warnings, details

    if yaml is None:
        errors.append("PyYAML required for task execution readiness checker")
        return errors, warnings, details

    missing_by_task: dict[str, list[str]] = {}
    for rel in target_tasks:
        p = repo / rel
        if not p.is_file():
            errors.append(f"missing task file referenced for readiness check: {rel}")
            continue
        try:
            task_doc = load_yaml_file(p)
        except Exception as e:
            errors.append(f"task parse failure for {rel}: {e}")
            continue
        if not isinstance(task_doc, dict):
            errors.append(f"task file must be a YAML object: {rel}")
            continue

        missing = _missing_readiness_fields(task_doc.get("execution_readiness"))
        if missing:
            missing_by_task[rel] = missing
            errors.append(
                f"execution readiness incomplete for {rel}; missing fields: {', '.join(missing)}"
            )

    details["missing_by_task"] = missing_by_task
    if missing_by_task:
        errors.append(
            "remediation: populate .pm/tasks/<task>.yml.execution_readiness with all required fields "
            "(objective, scope, constraints, assumptions, decision rationale, alternatives considered, "
            "dependencies, acceptance criteria, validation plan, rollback/risk, open questions)"
        )

    return errors, warnings, details


def checker_map() -> dict[str, CheckerFn]:
    return {
        "open_question_taskization": check_open_question_taskization,
        "task_execution_readiness": check_task_execution_readiness,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enforce PM runtime toggle checks")
    p.add_argument("target", nargs="?", default=".", help="Repo root")
    p.add_argument("--json", action="store_true", help="Emit JSON output")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.target).resolve()

    project_cfg, cfg_errors, cfg_warnings = load_project_cfg(repo)
    if cfg_errors:
        payload = {"ok": False, "errors": cfg_errors, "warnings": cfg_warnings}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for e in cfg_errors:
                print(f"ERROR: {e}")
            for w in cfg_warnings:
                print(f"WARN: {w}")
        return 1

    toggles, t_errors, t_warnings = resolve_effective_toggles(project_cfg)
    registry, r_errors, r_warnings = load_registry(repo, project_cfg)
    staged = staged_files(repo)

    errors = [*t_errors, *r_errors]
    warnings = [*cfg_warnings, *t_warnings, *r_warnings]
    checks: list[dict[str, Any]] = []

    toggles_map = registry.get("toggles", {}) if isinstance(registry, dict) else {}
    if not isinstance(toggles_map, dict):
        toggles_map = {}

    handlers = checker_map()
    fail_fallback = fail_on_builtin_fallback(project_cfg)

    for toggle_name, enabled in sorted(toggles.items()):
        if not enabled:
            checks.append({"toggle": toggle_name, "enabled": False, "skipped": True})
            continue

        reg = toggles_map.get(toggle_name)
        if not isinstance(reg, dict):
            errors.append(f"enabled toggle missing from registry: {toggle_name}")
            checks.append({"toggle": toggle_name, "enabled": True, "ok": False})
            continue

        checker_id = str(reg.get("checker", "")).strip()
        fn, resolve_err, resolve_warn, used_fallback = resolve_checker(repo, checker_id, handlers, registry)
        if fn is None:
            errors.append(
                f"enabled toggle {toggle_name} {resolve_err or f'references unknown checker: {checker_id!r}'}"
            )
            checks.append(
                {
                    "toggle": toggle_name,
                    "enabled": True,
                    "checker": checker_id,
                    "ok": False,
                }
            )
            continue
        if resolve_warn:
            if used_fallback and fail_fallback:
                errors.append(f"{toggle_name}: builtin fallback disallowed: {resolve_warn}")
            else:
                warnings.append(f"{toggle_name}: {resolve_warn}")

        try:
            c_errors, c_warnings, details = fn(repo, reg, staged)
        except Exception as e:
            errors.append(f"{toggle_name}: checker runtime failure: {e}")
            checks.append(
                {
                    "toggle": toggle_name,
                    "enabled": True,
                    "checker": checker_id,
                    "ok": False,
                }
            )
            continue
        errors.extend(f"{toggle_name}: {x}" for x in c_errors)
        warnings.extend(f"{toggle_name}: {x}" for x in c_warnings)
        checks.append(
            {
                "toggle": toggle_name,
                "enabled": True,
                "checker": checker_id,
                "ok": len(c_errors) == 0,
                "details": details,
            }
        )

    ok = len(errors) == 0
    payload = {
        "ok": ok,
        "repo": str(repo),
        "staged_files": staged,
        "enabled_toggles": sorted([k for k, v in toggles.items() if v]),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for w in warnings:
            print(f"WARN: {w}")
        for c in checks:
            name = c.get("toggle")
            if c.get("enabled") is False:
                print(f"INFO: toggle disabled: {name}")
            elif c.get("ok"):
                print(f"OK: toggle check passed: {name}")
        if not ok:
            print("ERROR: PM toggle checks failed:")
            for e in errors:
                print(f" - {e}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
