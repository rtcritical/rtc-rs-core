#!/usr/bin/env python3
"""pm_runtime_brief_lib.py

Build deterministic PM runtime brief content from active facets + lock state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> Any:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if data is not None else {}


def _facet_lock_index(lock_data: Any) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    facets = lock_data.get("facets", []) if isinstance(lock_data, dict) else []
    if not isinstance(facets, list):
        return out
    for rec in facets:
        if not isinstance(rec, dict):
            continue
        fid = str(rec.get("id", "")).strip()
        if not fid:
            continue
        out[fid] = {
            "version": str(rec.get("version", "")).strip(),
            "digest": str(rec.get("digest", "")).strip(),
            "source": str(rec.get("source", "")).strip(),
            "mode": str(rec.get("mode", "")).strip(),
            "path": str(rec.get("path", "")).strip(),
        }
    return out


def _facet_reads(project_root: Path, facet_id: str) -> list[str]:
    facet_dir = project_root / ".pm" / "facets" / facet_id
    out: list[str] = []
    for sub in ("policies", "procedures"):
        base = facet_dir / sub
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            rel = p.relative_to(project_root).as_posix()
            out.append(rel)
    return out


def build_runtime_brief(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    pm_dir = project_root / ".pm"
    project_cfg = _load_yaml(pm_dir / "project.yml")
    lock_data = _load_yaml(pm_dir / "facet.lock.yml")

    active = project_cfg.get("active_facets", []) if isinstance(project_cfg, dict) else []
    if not isinstance(active, list):
        active = []
    active_facets = [str(x).strip() for x in active if str(x).strip()]

    lock_idx = _facet_lock_index(lock_data)

    facets: list[dict[str, Any]] = []
    facet_overlay_reads: list[str] = []
    for fid in active_facets:
        rec = lock_idx.get(fid, {})
        reads = _facet_reads(project_root, fid)
        facet_overlay_reads.extend(reads)
        facets.append(
            {
                "id": fid,
                "version": rec.get("version", ""),
                "digest": rec.get("digest", ""),
                "source": rec.get("source", ""),
                "mode": rec.get("mode", ""),
                "path": rec.get("path", f".pm/facets/{fid}"),
                "required_reads": reads,
            }
        )

    kernel_required_inputs = [
        ".pm/procedures/pm-operations.md",
        ".pm/charter.md",
        ".pm/goals.md",
        ".pm/scope.md",
        ".pm/backlog.md",
    ]

    required_checks = [
        "python3 scripts/check_pm_runtime_brief.py <project-path>",
        "python3 scripts/run_facet_checks.py <project-path>",
    ]

    brief: dict[str, Any] = {
        "schema_version": 1,
        "brief_id": "pm-runtime-brief-v1",
        "authority": {
            "description": "Deterministic PM runtime read/check contract derived from active facets.",
            "source_of_truth": [
                ".pm/project.yml",
                ".pm/facet.lock.yml",
                ".pm/facets/<facet-id>/policies/*.md",
                ".pm/facets/<facet-id>/procedures/*.md",
            ],
        },
        "kernel_required_inputs": kernel_required_inputs,
        "active_facets": facets,
        "facet_overlay_required_reads": sorted(set(facet_overlay_reads)),
        "required_checks": required_checks,
    }
    return brief


def dump_runtime_brief_yaml(brief: dict[str, Any]) -> str:
    return yaml.safe_dump(brief, sort_keys=False, allow_unicode=False)
