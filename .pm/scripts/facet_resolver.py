#!/usr/bin/env python3
"""facet_resolver.py

What:
  Resolve active facets into deterministic `.pm/generated/facet-plan.yml`.

Why:
  Implements T-042 facet runtime resolver contract v0 with dependency/conflict
  validation and ordered-last-wins merge semantics.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from pm_runtime_brief_lib import build_runtime_brief, dump_runtime_brief_yaml

FACET_ID_RE = re.compile(r"^[a-z0-9]+([.-][a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
REMOVED_LEGACY_FACET_IDS = {"pm." + "core-governance"}


@dataclass
class Diagnostic:
    level: str
    code: str
    message: str
    facet: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out = {"level": self.level, "code": self.code, "message": self.message}
        if self.facet:
            out["facet"] = self.facet
        return out


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resolve active facets into generated facet plan")
    p.add_argument("project", nargs="?", default=".", help="Project root")
    p.add_argument("--project-config", default=".pm/project.yml", help="Project facet config path (relative to project)")
    p.add_argument("--facets-dir", default=".pm/facets", help="Installed facets directory (relative to project)")
    p.add_argument("--out", default=".pm/generated/facet-plan.yml", help="Output plan path (relative to project)")
    p.add_argument("--resolver-version", default="facet-resolver-v0", help="Resolver version value")
    p.add_argument("--dry-run", action="store_true", help="Validate/resolve but do not write output")
    return p.parse_args()


def normalize_project_config(raw: Any) -> tuple[list[str], str, list[str]]:
    if not isinstance(raw, dict):
        return [], "ordered-last-wins", ["project config must be a YAML object"]

    active = raw.get("active_facets", [])
    merge_strategy = str(raw.get("merge_strategy", "ordered-last-wins")).strip()
    errs: list[str] = []

    if not isinstance(active, list):
        errs.append("active_facets must be a list")
        active_list: list[str] = []
    else:
        active_list = []

    if isinstance(active, list):
        for x in active:
            facet_id = str(x).strip()
            if facet_id in REMOVED_LEGACY_FACET_IDS:
                errs.append(
                    f"legacy facet id {facet_id!r} is no longer supported; use canonical id 'pm.governance.core'"
                )
            active_list.append(facet_id)

    if merge_strategy != "ordered-last-wins":
        errs.append("merge_strategy must be 'ordered-last-wins' in v0")

    for facet_id in active_list:
        if not FACET_ID_RE.fullmatch(facet_id):
            errs.append(f"invalid facet id in active_facets: {facet_id!r}")

    return active_list, merge_strategy, errs


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_descriptor_paths(facets_dir: Path) -> list[Path]:
    if not facets_dir.is_dir():
        return []

    found: set[Path] = set()
    # Direct facet-pack layout: .pm/facets/<facet-id>/facet.yml (works for dirs + symlinks)
    for p in facets_dir.glob("*/facet.yml"):
        if p.is_file():
            found.add(p)
    # Allow nested layouts as a fallback.
    for p in facets_dir.glob("**/facet.yml"):
        if p.is_file():
            found.add(p)
    return sorted(found)


def validate_descriptor(doc: Any, source: Path) -> tuple[str | None, list[Diagnostic]]:
    diags: list[Diagnostic] = []
    if not isinstance(doc, dict):
        diags.append(Diagnostic("error", "descriptor.invalid_type", f"descriptor must be object: {source}"))
        return None, diags

    schema_version = doc.get("schema_version")
    if schema_version != 1:
        diags.append(Diagnostic("error", "descriptor.schema_version", f"schema_version must be 1: {source}"))

    facet = doc.get("facet")
    if not isinstance(facet, dict):
        diags.append(Diagnostic("error", "descriptor.facet_missing", f"missing/invalid facet object: {source}"))
        return None, diags

    facet_id = str(facet.get("id", "")).strip()
    version = str(facet.get("version", "")).strip()
    description = str(facet.get("description", "")).strip()

    if not FACET_ID_RE.fullmatch(facet_id):
        diags.append(Diagnostic("error", "descriptor.facet_id", f"invalid facet.id: {facet_id!r}"))
    if not SEMVER_RE.fullmatch(version):
        diags.append(Diagnostic("error", "descriptor.facet_version", f"invalid facet.version semver: {version!r}", facet=facet_id or None))
    if not description:
        diags.append(Diagnostic("error", "descriptor.facet_description", "facet.description is required", facet=facet_id or None))

    compatibility = doc.get("compatibility")
    if not isinstance(compatibility, dict) or not str(compatibility.get("pm_schema", "")).strip():
        diags.append(Diagnostic("error", "descriptor.compatibility", "compatibility.pm_schema is required", facet=facet_id or None))

    deps = doc.get("dependencies")
    if not isinstance(deps, dict):
        diags.append(Diagnostic("error", "descriptor.dependencies", "dependencies object is required", facet=facet_id or None))
    else:
        for key in ("requires", "conflicts"):
            val = deps.get(key)
            if not isinstance(val, list):
                diags.append(Diagnostic("error", "descriptor.dependencies_type", f"dependencies.{key} must be an array", facet=facet_id or None))
                continue
            bad = [str(x) for x in val if not FACET_ID_RE.fullmatch(str(x))]
            if bad:
                diags.append(Diagnostic("error", "descriptor.dependencies_item", f"dependencies.{key} has invalid ids: {bad}", facet=facet_id or None))

    contrib = doc.get("contributions")
    if not isinstance(contrib, dict):
        diags.append(Diagnostic("error", "descriptor.contributions", "contributions object is required", facet=facet_id or None))

    return (facet_id if facet_id else None), diags


def merge_values(lhs: Any, rhs: Any) -> Any:
    if isinstance(lhs, dict) and isinstance(rhs, dict):
        out: dict[str, Any] = {k: lhs[k] for k in lhs}
        for k, v in rhs.items():
            if k in out:
                out[k] = merge_values(out[k], v)
            else:
                out[k] = v
        return out
    if isinstance(lhs, list) and isinstance(rhs, list):
        return [*lhs, *rhs]
    return rhs


def sort_keys_deep(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: sort_keys_deep(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [sort_keys_deep(v) for v in value]
    return value


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    project_config_path = project / args.project_config
    facets_dir = project / args.facets_dir
    out_path = project / args.out

    diagnostics: list[Diagnostic] = []

    if not project_config_path.is_file():
        diagnostics.append(Diagnostic("error", "project_config.missing", f"missing project facet config: {project_config_path}"))
    else:
        try:
            project_cfg = load_yaml(project_config_path)
        except Exception as e:
            diagnostics.append(Diagnostic("error", "project_config.parse", f"failed to parse project config: {e}"))
            project_cfg = None

    if diagnostics:
        for d in diagnostics:
            print(f"ERROR: {d.code}: {d.message}", file=sys.stderr)
        return 1

    active_facets, merge_strategy, cfg_errors = normalize_project_config(project_cfg)
    for msg in cfg_errors:
        diagnostics.append(Diagnostic("error", "project_config.invalid", msg))

    # Duplicate activation check
    seen: set[str] = set()
    dupes: list[str] = []
    for facet_id in active_facets:
        if facet_id in seen:
            dupes.append(facet_id)
        seen.add(facet_id)
    for dup in sorted(set(dupes)):
        diagnostics.append(Diagnostic("error", "activation.duplicate", f"duplicate active facet id: {dup}", facet=dup))

    descriptor_index: dict[str, tuple[dict[str, Any], Path]] = {}
    for desc_path in find_descriptor_paths(facets_dir):
        try:
            doc = load_yaml(desc_path)
        except Exception as e:
            diagnostics.append(Diagnostic("error", "descriptor.parse", f"failed to parse {desc_path}: {e}"))
            continue
        facet_id, d_diags = validate_descriptor(doc, desc_path)
        diagnostics.extend(d_diags)
        if facet_id:
            if facet_id in descriptor_index:
                diagnostics.append(Diagnostic("error", "descriptor.duplicate_id", f"duplicate descriptor facet id across files: {facet_id}", facet=facet_id))
            else:
                descriptor_index[facet_id] = (doc, desc_path)

    active_docs: list[tuple[str, dict[str, Any]]] = []
    for facet_id in active_facets:
        entry = descriptor_index.get(facet_id)
        if not entry:
            diagnostics.append(Diagnostic("error", "activation.missing_descriptor", f"active facet has no installed descriptor: {facet_id}", facet=facet_id))
            continue
        active_docs.append((facet_id, entry[0]))

    active_set = set(active_facets)
    for facet_id, doc in active_docs:
        deps = doc.get("dependencies", {}) if isinstance(doc, dict) else {}
        reqs = deps.get("requires", []) if isinstance(deps, dict) else []
        conflicts = deps.get("conflicts", []) if isinstance(deps, dict) else []

        for req in reqs:
            req_s = str(req)
            if req_s not in active_set:
                diagnostics.append(Diagnostic("error", "dependency.unsatisfied", f"required facet is not active: {req_s}", facet=facet_id))

        for conf in conflicts:
            conf_s = str(conf)
            if conf_s in active_set:
                diagnostics.append(Diagnostic("error", "dependency.conflict", f"conflicting facet active: {conf_s}", facet=facet_id))

    merged: dict[str, Any] = {}
    for facet_id, doc in active_docs:
        contrib = doc.get("contributions", {}) if isinstance(doc, dict) else {}
        if isinstance(contrib, dict):
            merged = merge_values(merged, contrib)
        diagnostics.append(Diagnostic("info", "facet.applied", f"applied contributions from {facet_id}", facet=facet_id))

    plan = {
        "schema_version": 1,
        "resolved_at": utc_now(),
        "resolver_version": args.resolver_version,
        "merge_strategy": merge_strategy,
        "active_facets": active_facets,
        "diagnostics": [d.as_dict() for d in diagnostics],
        "merged": sort_keys_deep(merged),
    }

    has_error = any(d.level == "error" for d in diagnostics)
    if has_error:
        for d in diagnostics:
            if d.level == "error":
                print(f"ERROR: {d.code}: {d.message}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True))
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True), encoding="utf-8")
    brief_path = project / ".pm" / "generated" / "pm-runtime-brief.yml"
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief = build_runtime_brief(project)
    brief_path.write_text(dump_runtime_brief_yaml(brief), encoding="utf-8")
    print(f"OK: wrote {out_path}")
    print(f"OK: wrote {brief_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
