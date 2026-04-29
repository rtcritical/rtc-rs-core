#!/usr/bin/env python3
"""validate_pm.py

What:
  Validates `.pm` structure and content against baseline schema expectations.

Why:
  Provide a fast quality gate for onboarding, migration, and ongoing governance.

How:
  - Checks required files/directories
  - Validates manifest/stakeholder/backlog/intake structure
  - Validates PM Task Schema v2 canonical task files when present
  - Verifies generated backlog/closed view drift via render check
  - Supports stricter readiness checks via `--strict`

Usage:
  python3 scripts/validate_pm.py <project-path>
  python3 scripts/validate_pm.py <project-path> --strict
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

REQUIRED_FILES = [
    "manifest.yml",
    "charter.md",
    "goals.md",
    "scope.md",
    "backlog.md",
    "stakeholders.yml",
    "inbox/README.md",
    "project.yml",
]

REQUIRED_DIRS = [
    "decisions",
    "status",
    "inbox/raw",
    "inbox/assets",
]

LIFECYCLE_VALUES = {
    "intake",
    "chartering",
    "scoping",
    "planning",
    "execution",
    "maintenance",
    "archived",
}

BACKLOG_STATUSES = {"todo", "in-progress", "blocked", "done"}

V2_REQUIRED_FIELDS = {
    "schema_version",
    "task_id",
    "title",
    "epic_id",
    "priority",
    "status",
    "owner",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "depends_on",
    "context_refs",
    "intake_refs",
    "decision_refs",
    "evidence_refs",
    "risk_tier",
    "required_evidence",
    "timebox",
    "rollback_plan",
    "notes",
}

V2_STATUS = {"todo", "in_progress", "blocked", "done", "abandoned", "superseded"}
V2_TERMINAL = {"done", "abandoned", "superseded"}
V2_RISK = {"low", "medium", "high"}
V2_CLOSE_REASON = {"completed", "abandoned", "superseded", "duplicate", "invalid"}


def _as_list_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        s = str(item).strip()
        if s:
            out.append(s)
    return out


def _looks_like_design_handoff_checkpoint(task: dict[str, Any]) -> bool:
    title = str(task.get("title", "")).strip().lower()
    return "taskize implementation phase" in title


def validate_project_facet_config(pm: Path) -> int:
    failures = 0
    if yaml is None:
        warn("PyYAML not available; skipping project facet config validation")
        return failures

    p = pm / "project.yml"
    if not p.is_file():
        return failures

    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"project.yml parse failure: {e}")
        return 1

    if not isinstance(data, dict):
        err("project.yml must be a YAML object")
        return 1

    merge_strategy = str(data.get("merge_strategy", "")).strip()
    if merge_strategy != "ordered-last-wins":
        err("project.yml merge_strategy must be 'ordered-last-wins' for v0")
        failures += 1

    active = data.get("active_facets", [])
    if not isinstance(active, list):
        err("project.yml active_facets must be a list")
        failures += 1
    else:
        bad = [str(x) for x in active if re.fullmatch(r"[a-z0-9]+([.-][a-z0-9]+)*", str(x)) is None]
        if bad:
            err(f"project.yml active_facets contains invalid ids: {bad}")
            failures += 1
        if len(active) != len(set(str(x) for x in active)):
            err("project.yml active_facets must not contain duplicates")
            failures += 1

    context_policy = data.get("context_refs_policy")
    if context_policy is not None:
        if not isinstance(context_policy, dict):
            err("project.yml context_refs_policy must be an object when present")
            failures += 1
        else:
            allow_anchors = context_policy.get("allow_anchors")
            if allow_anchors is not None and not isinstance(allow_anchors, bool):
                err("project.yml context_refs_policy.allow_anchors must be boolean when present")
                failures += 1

    source_policy = data.get("facet_source_policy")
    if source_policy is not None:
        if not isinstance(source_policy, dict):
            err("project.yml facet_source_policy must be an object when present")
            failures += 1
        else:
            trusted = source_policy.get("trusted_prefixes")
            if trusted is not None:
                if not isinstance(trusted, list):
                    err("project.yml facet_source_policy.trusted_prefixes must be an array when present")
                    failures += 1
                else:
                    bad = [str(x) for x in trusted if not str(x).strip()]
                    if bad:
                        err("project.yml facet_source_policy.trusted_prefixes must not contain empty entries")
                        failures += 1

    strict_mode = data.get("strict_authority_mode")
    if strict_mode is not None:
        if not isinstance(strict_mode, dict):
            err("project.yml strict_authority_mode must be an object when present")
            failures += 1
        else:
            enabled = strict_mode.get("enabled")
            if enabled is not None and not isinstance(enabled, bool):
                err("project.yml strict_authority_mode.enabled must be boolean when present")
                failures += 1

            execution_mode = strict_mode.get("execution_mode")
            if execution_mode is not None:
                if not isinstance(execution_mode, dict):
                    err("project.yml strict_authority_mode.execution_mode must be an object when present")
                    failures += 1
                else:
                    preset = execution_mode.get("preset")
                    if preset is not None:
                        if str(preset) not in {"prototype", "balanced", "hardened"}:
                            err("project.yml strict_authority_mode.execution_mode.preset must be one of prototype|balanced|hardened")
                            failures += 1
                    overrides = execution_mode.get("overrides")
                    if overrides is not None:
                        if not isinstance(overrides, dict):
                            err("project.yml strict_authority_mode.execution_mode.overrides must be an object when present")
                            failures += 1
                        else:
                            for k, v in overrides.items():
                                if not isinstance(v, bool):
                                    err(
                                        "project.yml strict_authority_mode.execution_mode.overrides"
                                        f".{k} must be boolean"
                                    )
                                    failures += 1

            toggles = strict_mode.get("toggles")
            if toggles is not None:
                if not isinstance(toggles, dict):
                    err("project.yml strict_authority_mode.toggles must be an object when present")
                    failures += 1
                else:
                    for k, v in toggles.items():
                        if not isinstance(v, bool):
                            err(f"project.yml strict_authority_mode.toggles.{k} must be boolean")
                            failures += 1

            plugin_requirements = strict_mode.get("plugin_requirements")
            if plugin_requirements is not None:
                if not isinstance(plugin_requirements, dict):
                    err("project.yml strict_authority_mode.plugin_requirements must be an object when present")
                    failures += 1
                else:
                    fbf = plugin_requirements.get("fail_on_builtin_fallback")
                    if fbf is not None and not isinstance(fbf, bool):
                        err(
                            "project.yml strict_authority_mode.plugin_requirements"
                            ".fail_on_builtin_fallback must be boolean when present"
                        )
                        failures += 1

            governed_scope = strict_mode.get("governed_scope")
            if governed_scope is not None:
                if not isinstance(governed_scope, dict):
                    err("project.yml strict_authority_mode.governed_scope must be an object when present")
                    failures += 1
                else:
                    for key in ("include", "exclude"):
                        val = governed_scope.get(key)
                        if val is not None:
                            if not isinstance(val, list):
                                err(
                                    f"project.yml strict_authority_mode.governed_scope.{key} must be an array when present"
                                )
                                failures += 1
                            else:
                                bad = [str(x) for x in val if not str(x).strip()]
                                if bad:
                                    err(
                                        f"project.yml strict_authority_mode.governed_scope.{key} must not contain empty entries"
                                    )
                                    failures += 1

    return failures


def _load_project_allow_anchors(pm: Path) -> bool:
    if yaml is None:
        return False
    p = pm / "project.yml"
    if not p.is_file():
        return False
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    policy = data.get("context_refs_policy")
    if not isinstance(policy, dict):
        return False
    return bool(policy.get("allow_anchors", False))


def _slugify_markdown_heading(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[`*_~]", "", s)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _collect_markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    txt = read_text(path)
    if not txt:
        return anchors
    for line in txt.splitlines():
        m = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if m:
            slug = _slugify_markdown_heading(m.group(1))
            if slug:
                anchors.add(slug)
    for m in re.finditer(r"<a\s+id=[\"']([^\"']+)[\"']", txt, flags=re.IGNORECASE):
        anchors.add(m.group(1).strip())
    return anchors


def validate_facet_lock(pm: Path) -> int:
    failures = 0
    if yaml is None:
        warn("PyYAML not available; skipping facet lock validation")
        return failures

    p = pm / "facet.lock.yml"
    if not p.is_file():
        return failures

    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"facet.lock.yml parse failure: {e}")
        return 1

    if not isinstance(data, dict):
        err("facet.lock.yml must be a YAML object")
        return 1

    if data.get("schema_version") != 1:
        err("facet.lock.yml schema_version must be 1")
        failures += 1

    facets = data.get("facets")
    if not isinstance(facets, list):
        err("facet.lock.yml facets must be an array")
        return failures + 1

    seen: set[str] = set()
    for rec in facets:
        if not isinstance(rec, dict):
            err("facet.lock.yml facet entry must be an object")
            failures += 1
            continue
        for req in ["id", "version", "source", "digest", "installed_at"]:
            if not str(rec.get(req, "")).strip():
                err(f"facet.lock.yml missing required field in facet entry: {req}")
                failures += 1
        fid = str(rec.get("id", "")).strip()
        if fid:
            if re.fullmatch(r"[a-z0-9]+([.-][a-z0-9]+)*", fid) is None:
                err(f"facet.lock.yml invalid facet id: {fid!r}")
                failures += 1
            if fid in seen:
                err(f"facet.lock.yml duplicate facet id entry: {fid}")
                failures += 1
            seen.add(fid)
        digest = str(rec.get("digest", "")).strip()
        if digest and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
            err(f"facet.lock.yml invalid digest: {digest!r}")
            failures += 1
        mode = str(rec.get("mode", "")).strip()
        if mode and mode not in {"copy", "symlink"}:
            err(f"facet.lock.yml invalid mode: {mode!r}")
            failures += 1

    return failures


def _find_installed_facet_ids(pm: Path) -> tuple[set[str], list[str]]:
    ids: set[str] = set()
    errs: list[str] = []
    facets_dir = pm / "facets"
    if not facets_dir.is_dir() or yaml is None:
        return ids, errs

    seen_paths: set[Path] = set()
    paths = list(facets_dir.glob("*/facet.yml")) + list(facets_dir.glob("**/facet.yml"))
    for p in sorted(paths):
        if p in seen_paths or not p.is_file():
            continue
        seen_paths.add(p)
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
            if not isinstance(doc, dict) or not isinstance(doc.get("facet"), dict):
                raise ValueError("missing facet object")
            fid = str(doc["facet"].get("id", "")).strip()
            if not fid:
                raise ValueError("missing facet.id")
            ids.add(fid)
        except Exception as e:
            errs.append(f"invalid installed descriptor {p}: {e}")

    return ids, errs


def validate_facet_runtime_consistency(pm: Path) -> int:
    failures = 0
    if yaml is None:
        warn("PyYAML not available; skipping facet runtime consistency validation")
        return failures

    cfg_path = pm / "project.yml"
    lock_path = pm / "facet.lock.yml"
    if not cfg_path.is_file() and not lock_path.is_file():
        return failures

    active: list[str] = []
    if cfg_path.is_file():
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            if isinstance(cfg, dict) and isinstance(cfg.get("active_facets"), list):
                active = [str(x).strip() for x in cfg.get("active_facets", []) if str(x).strip()]
        except Exception as e:
            err(f"project.yml parse failure during consistency check: {e}")
            return 1

    lock_ids: set[str] = set()
    if lock_path.is_file():
        try:
            lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
            if isinstance(lock, dict) and isinstance(lock.get("facets"), list):
                for rec in lock.get("facets", []):
                    if isinstance(rec, dict):
                        fid = str(rec.get("id", "")).strip()
                        if fid:
                            lock_ids.add(fid)
        except Exception as e:
            err(f"facet.lock.yml parse failure during consistency check: {e}")
            return 1

    installed_ids, parse_errs = _find_installed_facet_ids(pm)
    for msg in parse_errs:
        err(msg)
        failures += 1

    for fid in sorted(set(active) - installed_ids):
        err(f"facet consistency: active facet missing installed descriptor: {fid}")
        failures += 1
    for fid in sorted(lock_ids - installed_ids):
        err(f"facet consistency: lock facet missing installed descriptor: {fid}")
        failures += 1
    for fid in sorted(set(active) - lock_ids):
        err(f"facet consistency: active facet missing lock pin: {fid}")
        failures += 1
    for fid in sorted(installed_ids - lock_ids):
        warn(f"facet consistency: installed facet missing lock pin: {fid}")

    return failures


def validate_version_alignment(pm: Path) -> int:
    failures = 0
    if yaml is None:
        warn("PyYAML not available; skipping version alignment validation")
        return failures

    version_path = pm / "version.yml"
    manifest_path = pm / "manifest.yml"
    tasks_dir = pm / "tasks"
    has_v2_tasks = tasks_dir.is_dir() and any(tasks_dir.glob("T-*.yml"))

    version_data = None
    manifest_data = None
    if version_path.is_file():
        try:
            version_data = yaml.safe_load(version_path.read_text(encoding="utf-8"))
        except Exception as e:
            err(f"version.yml parse failure: {e}")
            return failures + 1
    if manifest_path.is_file():
        try:
            manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            err(f"manifest.yml parse failure during version alignment check: {e}")
            return failures + 1

    pm_meta = version_data.get("pm") if isinstance(version_data, dict) else None
    schema_meta = manifest_data.get("schema") if isinstance(manifest_data, dict) else None

    pm_schema_version = str(pm_meta.get("schema_version", "")).strip() if isinstance(pm_meta, dict) else ""
    pm_compat = str(pm_meta.get("compatibility", "")).strip() if isinstance(pm_meta, dict) else ""
    manifest_schema_version = str(schema_meta.get("version", "")).strip() if isinstance(schema_meta, dict) else ""
    manifest_compat = str(schema_meta.get("compatibility", "")).strip() if isinstance(schema_meta, dict) else ""

    if has_v2_tasks:
        if not pm_schema_version.startswith("2"):
            err("version.yml pm.schema_version must start with '2' when .pm/tasks/T-*.yml exists")
            failures += 1
        if "<3.0.0" not in pm_compat:
            err("version.yml pm.compatibility must target v2 range (expected '<3.0.0') when v2 tasks exist")
            failures += 1
        if manifest_schema_version and not manifest_schema_version.startswith("2"):
            err("manifest.yml schema.version must start with '2' when v2 tasks exist")
            failures += 1
        if manifest_compat and "<3.0.0" not in manifest_compat:
            err("manifest.yml schema.compatibility must target v2 range (expected '<3.0.0') when v2 tasks exist")
            failures += 1

    if pm_schema_version and manifest_schema_version and pm_schema_version != manifest_schema_version:
        err(
            f"version mismatch: .pm/version.yml pm.schema_version={pm_schema_version!r} "
            f"!= .pm/manifest.yml schema.version={manifest_schema_version!r}"
        )
        failures += 1

    if pm_compat and manifest_compat and pm_compat != manifest_compat:
        err(
            f"compatibility mismatch: .pm/version.yml pm.compatibility={pm_compat!r} "
            f"!= .pm/manifest.yml schema.compatibility={manifest_compat!r}"
        )
        failures += 1

    return failures


def err(msg: str) -> None:
    print(f"ERROR: {msg}")


def warn(msg: str) -> None:
    print(f"WARN: {msg}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        err(f"Cannot read {path}: {e}")
        return ""


def validate_manifest(pm: Path) -> int:
    failures = 0
    mpath = pm / "manifest.yml"

    if yaml is None:
        warn("PyYAML not available; skipping deep manifest validation")
        return failures

    try:
        data = yaml.safe_load(mpath.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"manifest.yml parse failure: {e}")
        return 1

    if not isinstance(data, dict):
        err("manifest.yml must be a YAML object")
        return 1

    project = data.get("project")
    lifecycle = project.get("lifecycle") if isinstance(project, dict) else None
    if lifecycle not in LIFECYCLE_VALUES:
        err(f"manifest lifecycle must be one of {sorted(LIFECYCLE_VALUES)}; got {lifecycle!r}")
        failures += 1

    for top in ["project", "owners", "links", "updated"]:
        if top not in data:
            err(f"manifest missing top-level key: {top}")
            failures += 1

    return failures


def validate_backlog(pm: Path, strict: bool = False) -> int:
    failures = 0
    b = read_text(pm / "backlog.md")

    if "## Epic Mapping" not in b:
        err("backlog.md missing '## Epic Mapping' section")
        failures += 1
    if "## Task List" not in b:
        err("backlog.md missing '## Task List' section")
        failures += 1

    if strict:
        # Require at least one data row in task table with ID and valid status token.
        task_row = re.search(
            r"(?im)^\|\s*T-\d+\s*\|\s*E-\d+\s*\|.*\|\s*(todo|in-progress|blocked|done|abandoned|superseded)\s*\|",
            b,
        )
        if not task_row:
            err("strict: backlog task table must include at least one valid task row (T-*, E-*, status)")
            failures += 1
    else:
        statuses = set(re.findall(r"\|\s*([A-Za-z-]+)\s*\|", b))
        known = {s.lower() for s in statuses if s.lower() in BACKLOG_STATUSES}
        if not known:
            warn("backlog.md has no recognized status values yet (ok for very early drafts)")

    return failures


def validate_stakeholders(pm: Path, strict: bool = False) -> int:
    failures = 0
    spath = pm / "stakeholders.yml"

    if yaml is None:
        warn("PyYAML not available; skipping deep stakeholders validation")
        return failures

    try:
        data = yaml.safe_load(spath.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"stakeholders.yml parse failure: {e}")
        return 1

    if not isinstance(data, dict):
        err("stakeholders.yml must be a YAML object")
        return 1

    stakeholders = data.get("stakeholders")
    if not isinstance(stakeholders, list) or len(stakeholders) == 0:
        err("stakeholders.yml must contain non-empty stakeholders list")
        return 1

    if strict:
        has_non_placeholder = False
        for item in stakeholders:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            role = str(item.get("role", "")).strip()
            if name and "REPLACE_" not in name and role:
                has_non_placeholder = True
                break
        if not has_non_placeholder:
            err("strict: stakeholders.yml must include at least one non-placeholder stakeholder with name+role")
            failures += 1

    return failures


def validate_intake_notes(pm: Path, strict: bool = False) -> int:
    failures = 0
    raw_dir = pm / "inbox" / "raw"
    notes = sorted(raw_dir.glob("*.md"))

    if strict and not notes:
        err("strict: .pm/inbox/raw must contain at least one intake note")
        return 1

    required_headers = ["captured_at", "source_type", "source_ref", "captured_by"]
    for note in notes:
        txt = read_text(note)
        if not txt:
            continue

        if "# Intake Note" not in txt:
            if strict:
                err(f"strict: intake note missing '# Intake Note': {note.name}")
                failures += 1
            continue

        for h in required_headers:
            if re.search(rf"(?m)^-\s*{re.escape(h)}\s*:\s*.+$", txt) is None:
                msg = f"intake note missing header '{h}': {note.name}"
                if strict:
                    err(f"strict: {msg}")
                    failures += 1
                else:
                    warn(msg)

        if strict:
            if "## Raw Content" not in txt:
                err(f"strict: intake note missing '## Raw Content': {note.name}")
                failures += 1
            if "## Synthesis Candidates" not in txt:
                err(f"strict: intake note missing '## Synthesis Candidates': {note.name}")
                failures += 1

    return failures


def _validate_actor(actor: Any, field_name: str, file_name: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(actor, dict):
        return [f"{file_name}: {field_name} must be an object"]
    atype = str(actor.get("type", "")).strip()
    aid = str(actor.get("id", "")).strip()
    if atype not in {"human", "agent", "system"}:
        issues.append(f"{file_name}: {field_name}.type invalid: {atype!r}")
    if not aid:
        issues.append(f"{file_name}: {field_name}.id is required")
    if atype in {"agent", "system"} and actor.get("run_id", None) in (None, ""):
        issues.append(f"{file_name}: {field_name}.run_id required for agent/system")
    return issues


def validate_tasks_v2(pm: Path, strict: bool = False) -> int:
    failures = 0
    allow_context_anchors = _load_project_allow_anchors(pm)
    tasks_dir = pm / "tasks"
    files = sorted(tasks_dir.glob("T-*.yml"))
    if not files:
        if strict:
            err("strict: .pm/tasks exists but has no T-*.yml task files")
            return 1
        return 0

    loaded: dict[str, tuple[Path, dict[str, Any]]] = {}
    for f in files:
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) if yaml else None
        except Exception as e:
            err(f"{f.name}: YAML parse error: {e}")
            failures += 1
            continue
        if not isinstance(data, dict):
            err(f"{f.name}: task file must be YAML object")
            failures += 1
            continue
        task_id = str(data.get("task_id", "")).strip()
        if re.fullmatch(r"T-\d+", task_id):
            loaded[task_id] = (f, data)

    seen_ids: set[str] = set()
    for f in files:
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) if yaml else None
        except Exception as e:
            err(f"{f.name}: YAML parse error: {e}")
            failures += 1
            continue

        if not isinstance(data, dict):
            err(f"{f.name}: task file must be YAML object")
            failures += 1
            continue

        missing = sorted(k for k in V2_REQUIRED_FIELDS if k not in data)
        if missing:
            err(f"{f.name}: missing required fields: {', '.join(missing)}")
            failures += 1

        task_id = str(data.get("task_id", "")).strip()
        if not re.fullmatch(r"T-\d+", task_id):
            err(f"{f.name}: invalid task_id: {task_id!r}")
            failures += 1
        else:
            if task_id in seen_ids:
                err(f"{f.name}: duplicate task_id: {task_id}")
                failures += 1
            seen_ids.add(task_id)
            if f.stem != task_id:
                err(f"{f.name}: filename stem must match task_id ({task_id})")
                failures += 1

        schema_version = data.get("schema_version")
        if schema_version != 2:
            err(f"{f.name}: schema_version must be 2")
            failures += 1

        status = str(data.get("status", "")).strip()
        if status not in V2_STATUS:
            err(f"{f.name}: invalid status: {status!r}")
            failures += 1

        risk_tier = str(data.get("risk_tier", "")).strip()
        if risk_tier not in V2_RISK:
            err(f"{f.name}: invalid risk_tier: {risk_tier!r}")
            failures += 1

        for field_name in ["owner", "created_by", "updated_by"]:
            for issue in _validate_actor(data.get(field_name), field_name, f.name):
                err(issue)
                failures += 1

        context_refs = data.get("context_refs")
        intake_refs = data.get("intake_refs")
        decision_refs = data.get("decision_refs")
        evidence_refs = data.get("evidence_refs")
        if not isinstance(context_refs, list) or len(context_refs) == 0:
            err(f"{f.name}: context_refs must be a non-empty list")
            failures += 1
        else:
            for ref in context_refs:
                ref_s = str(ref).strip()
                if not ref_s:
                    err(f"{f.name}: context_refs entries must be non-empty strings")
                    failures += 1
                    continue
                base_ref, anchor = (ref_s.split("#", 1) + [""])[:2] if "#" in ref_s else (ref_s, "")
                if anchor and not allow_context_anchors:
                    err(f"{f.name}: context_refs must not include anchors/fragments: {ref_s!r}")
                    failures += 1
                    continue
                if not base_ref.startswith(".pm/"):
                    err(f"{f.name}: context_refs must point to internal PM paths (.pm/*): {ref_s!r}")
                    failures += 1
                    continue
                ref_path = (pm.parent / base_ref).resolve()
                if not str(ref_path).startswith(str(pm.resolve()) + "/"):
                    err(f"{f.name}: context_refs path escapes .pm directory: {ref_s!r}")
                    failures += 1
                    continue
                if not ref_path.exists():
                    err(f"{f.name}: context_refs path missing on disk: {ref_s!r}")
                    failures += 1
                    continue
                if anchor and allow_context_anchors:
                    if ref_path.suffix.lower() in {".md", ".markdown"}:
                        known = _collect_markdown_anchors(ref_path)
                        if anchor not in known:
                            warn(
                                f"{f.name}: context_refs anchor unresolved (best effort): {ref_s!r}"
                            )
                    else:
                        warn(
                            f"{f.name}: context_refs anchor check skipped for non-markdown path: {ref_s!r}"
                        )
        if not isinstance(intake_refs, list) or len(intake_refs) == 0:
            err(f"{f.name}: intake_refs must be a non-empty list")
            failures += 1
        if not isinstance(decision_refs, list):
            err(f"{f.name}: decision_refs must be a list")
            failures += 1
        if not isinstance(evidence_refs, list):
            err(f"{f.name}: evidence_refs must be a list")
            failures += 1

        handoff_required = data.get("handoff_required", False)
        if handoff_required not in {True, False}:
            err(f"{f.name}: handoff_required must be boolean when present")
            failures += 1
            handoff_required = False

        handoff_terminal_allowed = data.get("handoff_terminal_allowed", False)
        if handoff_terminal_allowed not in {True, False}:
            err(f"{f.name}: handoff_terminal_allowed must be boolean when present")
            failures += 1
            handoff_terminal_allowed = False

        handoff_terminal_reason = str(data.get("handoff_terminal_reason", "")).strip()
        handoff_terminal_ref = str(data.get("handoff_terminal_ref", "")).strip()

        if _looks_like_design_handoff_checkpoint(data) and status in V2_TERMINAL and handoff_required is not True:
            err(
                f"{f.name}: design->implementation checkpoint task must set handoff_required: true "
                f"before terminal closure"
            )
            failures += 1

        next_phase = data.get("next_phase_task_ids", [])
        if "next_phase_task_ids" in data and not isinstance(next_phase, list):
            err(f"{f.name}: next_phase_task_ids must be a list when present")
            failures += 1
            next_phase = []

        if handoff_required:
            if not isinstance(next_phase, list) or len(next_phase) == 0:
                err(f"{f.name}: handoff_required=true requires non-empty next_phase_task_ids")
                failures += 1
            else:
                bad_ids = [str(x) for x in next_phase if re.fullmatch(r"T-\d+", str(x).strip()) is None]
                if bad_ids:
                    err(f"{f.name}: next_phase_task_ids contains invalid task ids: {bad_ids}")
                    failures += 1
                unresolved = [str(x).strip() for x in next_phase if str(x).strip() not in loaded]
                if unresolved:
                    err(f"{f.name}: next_phase_task_ids references missing task files: {unresolved}")
                    failures += 1
                else:
                    successor_statuses = [
                        str((loaded[str(x).strip()][1]).get("status", "")).strip()
                        for x in next_phase
                        if str(x).strip() in loaded
                    ]
                    if status in V2_TERMINAL and all(s in V2_TERMINAL for s in successor_statuses):
                        if handoff_terminal_allowed:
                            if not handoff_terminal_reason:
                                err(
                                    f"{f.name}: handoff_terminal_allowed=true requires "
                                    "handoff_terminal_reason"
                                )
                                failures += 1
                            if not handoff_terminal_ref:
                                err(
                                    f"{f.name}: handoff_terminal_allowed=true requires "
                                    "handoff_terminal_ref"
                                )
                                failures += 1
                            elif not handoff_terminal_ref.startswith(".pm/decisions/"):
                                err(
                                    f"{f.name}: handoff_terminal_ref must point to .pm/decisions/*"
                                )
                                failures += 1
                            else:
                                ref_path = (pm.parent / handoff_terminal_ref).resolve()
                                if not str(ref_path).startswith(str(pm.resolve()) + "/") or not ref_path.exists():
                                    err(
                                        f"{f.name}: handoff_terminal_ref path missing on disk: "
                                        f"{handoff_terminal_ref!r}"
                                    )
                                    failures += 1
                        else:
                            err(
                                f"{f.name}: terminal handoff checkpoint requires at least one non-terminal "
                                f"next_phase_task_ids task"
                            )
                            failures += 1

        if status in V2_TERMINAL:
            for required in ["closed_at", "closed_by", "close_reason", "completion_evidence"]:
                if required not in data:
                    err(f"{f.name}: terminal task missing {required}")
                    failures += 1
            if str(data.get("close_reason", "")) not in V2_CLOSE_REASON:
                err(f"{f.name}: invalid close_reason: {data.get('close_reason')!r}")
                failures += 1
            for issue in _validate_actor(data.get("closed_by"), "closed_by", f.name):
                err(issue)
                failures += 1
            comp = data.get("completion_evidence")
            if not isinstance(comp, list) or len(comp) == 0:
                err(f"{f.name}: completion_evidence must be non-empty for terminal tasks")
                failures += 1
            if not isinstance(evidence_refs, list) or len(evidence_refs) == 0:
                err(f"{f.name}: evidence_refs must be non-empty for terminal tasks")
                failures += 1

    return failures


def validate_generated_view_drift(project_root: Path) -> int:
    # Prefer renderer shipped with this validator, fallback to target project local script.
    local_renderer = Path(__file__).resolve().parent / "render_pm_task_views.py"
    target_renderer = project_root / "scripts" / "render_pm_task_views.py"
    renderer = local_renderer if local_renderer.is_file() else target_renderer

    if not renderer.is_file():
        warn("render_pm_task_views.py not found; skipping generated-view drift check")
        return 0

    proc = subprocess.run([sys.executable, str(renderer), str(project_root), "--check", "--json"], capture_output=True, text=True)
    if proc.returncode == 0:
        return 0
    out = (proc.stdout or "") + (proc.stderr or "")
    msg = out.strip()
    try:
        payload = json.loads(proc.stdout or "{}")
        msg = f"backlog_changed={payload.get('backlog_changed')} closed_changed={payload.get('closed_changed')}"
    except Exception:
        pass
    err(f"generated view drift detected: {msg}")
    return 1


def validate_pm(pm: Path, strict: bool = False) -> int:
    failures = 0

    for rel in REQUIRED_FILES:
        p = pm / rel
        if not p.is_file():
            err(f"Missing required file: {rel}")
            failures += 1

    for rel in REQUIRED_DIRS:
        p = pm / rel
        if not p.is_dir():
            err(f"Missing required directory: {rel}")
            failures += 1

    if (pm / "manifest.yml").is_file():
        failures += validate_manifest(pm)
    if (pm / "version.yml").is_file() and (pm / "manifest.yml").is_file():
        failures += validate_version_alignment(pm)
    if (pm / "project.yml").is_file():
        failures += validate_project_facet_config(pm)
    if (pm / "facet.lock.yml").is_file():
        failures += validate_facet_lock(pm)
    failures += validate_facet_runtime_consistency(pm)
    if (pm / "backlog.md").is_file():
        failures += validate_backlog(pm, strict=strict)
    if (pm / "stakeholders.yml").is_file():
        failures += validate_stakeholders(pm, strict=strict)
    if (pm / "inbox" / "raw").is_dir():
        failures += validate_intake_notes(pm, strict=strict)

    tasks_dir = pm / "tasks"
    if tasks_dir.is_dir() and any(tasks_dir.glob("T-*.yml")):
        if yaml is None:
            err("PyYAML required for v2 task validation")
            failures += 1
        else:
            failures += validate_tasks_v2(pm, strict=strict)
            failures += validate_generated_view_drift(pm.parent)

    if failures == 0:
        if strict:
            print(f"OK (strict): {pm}")
        else:
            print(f"OK: {pm}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a .pm directory against rtc-openclaw-project-mgmt rules"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Path to project root or .pm directory",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable stricter checks for stakeholder realism, intake metadata, backlog rows, and v2 task contracts",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    pm = target if target.name == ".pm" else target / ".pm"

    if not pm.exists():
        err(f".pm not found at: {pm}")
        return 2
    if not pm.is_dir():
        err(f"Path exists but is not a directory: {pm}")
        return 2

    return 1 if validate_pm(pm, strict=args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
