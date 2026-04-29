#!/usr/bin/env python3
"""facet_lifecycle.py

What:
  Manage facet lifecycle for managed PM projects: discover/install/link/activate/
  deactivate/remove plus runtime status/resolve checks.

Why:
  Implements T-043/T-048/T-049/T-050 lifecycle and guardrail behavior.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

import yaml

FACET_ID_RE = re.compile(r"^[a-z0-9]+([.-][a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
REMOVED_LEGACY_FACET_IDS = {"pm." + "core-governance"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def reject_removed_legacy_id(facet_id: str) -> None:
    if facet_id in REMOVED_LEGACY_FACET_IDS:
        raise ValueError(
            f"legacy facet id {facet_id!r} is no longer supported; "
            "use canonical id 'pm.governance.core'"
        )


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def digest_descriptor(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()}"


def normalize_project_config(path: Path) -> dict[str, Any]:
    if path.is_file():
        raw = load_yaml(path)
        if not isinstance(raw, dict):
            raise ValueError("project config must be YAML object")
    else:
        raw = {}

    active = raw.get("active_facets", [])
    if not isinstance(active, list):
        raise ValueError("active_facets must be a list")
    active_ids_raw = [str(x).strip() for x in active if str(x).strip()]
    active_ids: list[str] = []
    for fid in active_ids_raw:
        reject_removed_legacy_id(fid)
        active_ids.append(fid)
    for fid in active_ids:
        if not FACET_ID_RE.fullmatch(fid):
            raise ValueError(f"invalid active facet id: {fid!r}")
    if len(active_ids) != len(set(active_ids)):
        raise ValueError("duplicate facet IDs in active_facets")

    merge = str(raw.get("merge_strategy", "ordered-last-wins")).strip()
    if merge != "ordered-last-wins":
        raise ValueError("merge_strategy must be 'ordered-last-wins' in v0")

    src_policy = raw.get("facet_source_policy", {})
    if src_policy is None:
        src_policy = {}
    if not isinstance(src_policy, dict):
        raise ValueError("facet_source_policy must be an object when present")
    trusted = src_policy.get("trusted_prefixes", [])
    if trusted is None:
        trusted = []
    if not isinstance(trusted, list) or any(not str(x).strip() for x in trusted):
        raise ValueError("facet_source_policy.trusted_prefixes must be an array of non-empty strings")

    return {
        "active_facets": active_ids,
        "merge_strategy": merge,
        "facet_source_policy": {"trusted_prefixes": [str(x).strip() for x in trusted]},
    }


def validate_descriptor(doc: Any, path: Path) -> tuple[str, str]:
    if not isinstance(doc, dict):
        raise ValueError(f"descriptor must be object: {path}")
    if doc.get("schema_version") != 1:
        raise ValueError(f"schema_version must be 1: {path}")

    facet = doc.get("facet")
    if not isinstance(facet, dict):
        raise ValueError(f"facet object required: {path}")

    fid = str(facet.get("id", "")).strip()
    version = str(facet.get("version", "")).strip()
    desc = str(facet.get("description", "")).strip()

    if not FACET_ID_RE.fullmatch(fid):
        raise ValueError(f"invalid facet.id: {fid!r}")
    if not SEMVER_RE.fullmatch(version):
        raise ValueError(f"invalid facet.version semver: {version!r}")
    if not desc:
        raise ValueError("facet.description is required")

    compatibility = doc.get("compatibility")
    if not isinstance(compatibility, dict) or not str(compatibility.get("pm_schema", "")).strip():
        raise ValueError("compatibility.pm_schema is required")

    deps = doc.get("dependencies")
    if not isinstance(deps, dict):
        raise ValueError("dependencies object is required")
    for key in ("requires", "conflicts"):
        vals = deps.get(key)
        if not isinstance(vals, list):
            raise ValueError(f"dependencies.{key} must be an array")
        for v in vals:
            if not FACET_ID_RE.fullmatch(str(v)):
                raise ValueError(f"dependencies.{key} has invalid facet id: {v!r}")

    contrib = doc.get("contributions")
    if not isinstance(contrib, dict):
        raise ValueError("contributions object is required")

    return fid, version


def read_lock(lock_path: Path) -> dict[str, Any]:
    if not lock_path.is_file():
        return {
            "schema_version": 1,
            "generated_at": utc_now(),
            "resolver_version": "facet-lifecycle-v0",
            "facets": [],
        }
    raw = load_yaml(lock_path)
    if not isinstance(raw, dict):
        raise ValueError("lockfile must be YAML object")
    if raw.get("schema_version") != 1:
        raise ValueError("lockfile schema_version must be 1")
    facets = raw.get("facets", [])
    if not isinstance(facets, list):
        raise ValueError("lockfile facets must be an array")
    return raw


def upsert_lock_entry(lock_data: dict[str, Any], entry: dict[str, Any]) -> None:
    facets = lock_data.setdefault("facets", [])
    if not isinstance(facets, list):
        raise ValueError("lockfile facets must be an array")

    replaced = False
    for i, rec in enumerate(facets):
        if isinstance(rec, dict) and str(rec.get("id", "")) == entry["id"]:
            facets[i] = entry
            replaced = True
            break
    if not replaced:
        facets.append(entry)

    facets.sort(key=lambda x: str(x.get("id", "")))
    lock_data["generated_at"] = utc_now()
    lock_data["resolver_version"] = "facet-lifecycle-v0"


def remove_lock_entry(lock_data: dict[str, Any], facet_id: str) -> None:
    facets = lock_data.get("facets", [])
    if not isinstance(facets, list):
        return
    lock_data["facets"] = [x for x in facets if not (isinstance(x, dict) and str(x.get("id", "")) == facet_id)]
    lock_data["generated_at"] = utc_now()
    lock_data["resolver_version"] = "facet-lifecycle-v0"


def lock_entry_by_id(lock_data: dict[str, Any], facet_id: str) -> dict[str, Any] | None:
    facets = lock_data.get("facets", [])
    if not isinstance(facets, list):
        return None
    for rec in facets:
        if isinstance(rec, dict) and str(rec.get("id", "")) == facet_id:
            return rec
    return None


def find_registry_descriptor(registry: Path, facet_id: str) -> Path:
    path = registry / facet_id / "facet.yml"
    if path.is_file():
        return path
    for p in sorted(registry.glob("**/facet.yml")):
        try:
            doc = load_yaml(p)
            if isinstance(doc, dict) and isinstance(doc.get("facet"), dict) and str(doc["facet"].get("id", "")).strip() == facet_id:
                return p
        except Exception:
            continue
    raise FileNotFoundError(f"facet id not found in registry: {facet_id}")


def check_source_trust(cfg: dict[str, Any], source_uri: str) -> None:
    trusted = cfg.get("facet_source_policy", {}).get("trusted_prefixes", [])
    if not trusted:
        return
    if not any(source_uri.startswith(prefix) for prefix in trusted):
        raise ValueError(
            f"source.untrusted: {source_uri!r} is outside trusted_prefixes {trusted}; "
            "update .pm/project.yml facet_source_policy.trusted_prefixes or choose a trusted source"
        )


def check_provenance(existing: dict[str, Any] | None, source_uri: str, digest: str, allow_source_change: bool, allow_digest_change: bool) -> None:
    if not existing:
        return

    old_source = str(existing.get("source", "")).strip()
    old_digest = str(existing.get("digest", "")).strip()

    if old_source and old_source != source_uri and not allow_source_change:
        raise ValueError(
            f"provenance.source_mismatch: existing source={old_source!r} new source={source_uri!r}; "
            "use --allow-source-change to override"
        )
    if old_digest and old_digest != digest and not allow_digest_change:
        raise ValueError(
            f"provenance.digest_mismatch: existing digest={old_digest!r} new digest={digest!r}; "
            "use --allow-digest-change to override"
        )


def install_from_descriptor(
    project: Path,
    descriptor_path: Path,
    mode: str,
    activate: bool,
    source_uri: str | None = None,
    allow_source_change: bool = False,
    allow_digest_change: bool = False,
) -> dict[str, Any]:
    doc = load_yaml(descriptor_path)
    facet_id, version = validate_descriptor(doc, descriptor_path)

    facet_src_dir = descriptor_path.parent
    source_uri = source_uri or str(facet_src_dir.resolve())
    descriptor_digest = digest_descriptor(descriptor_path)

    project_cfg_path = project / ".pm" / "project.yml"
    cfg = normalize_project_config(project_cfg_path)
    check_source_trust(cfg, source_uri)

    lock_path = project / ".pm" / "facet.lock.yml"
    lock_data = read_lock(lock_path)
    check_provenance(
        lock_entry_by_id(lock_data, facet_id),
        source_uri=source_uri,
        digest=descriptor_digest,
        allow_source_change=allow_source_change,
        allow_digest_change=allow_digest_change,
    )

    facets_dir = project / ".pm" / "facets"
    facets_dir.mkdir(parents=True, exist_ok=True)
    dest_dir = facets_dir / facet_id

    if dest_dir.exists() or dest_dir.is_symlink():
        if dest_dir.is_symlink() or dest_dir.is_file():
            dest_dir.unlink()
        else:
            shutil.rmtree(dest_dir)

    if mode == "copy":
        shutil.copytree(facet_src_dir, dest_dir)
    elif mode == "symlink":
        dest_dir.symlink_to(facet_src_dir.resolve())
    else:
        raise ValueError(f"unsupported mode: {mode}")

    if activate and facet_id not in cfg["active_facets"]:
        cfg["active_facets"].append(facet_id)
    save_yaml(project_cfg_path, cfg)

    lock_entry = {
        "id": facet_id,
        "version": version,
        "source": source_uri,
        "digest": descriptor_digest,
        "installed_at": utc_now(),
        "mode": mode,
        "path": str(dest_dir),
    }
    upsert_lock_entry(lock_data, lock_entry)
    save_yaml(lock_path, lock_data)

    return {
        "ok": True,
        "action": "install" if mode == "copy" else "link",
        "facet_id": facet_id,
        "version": version,
        "mode": mode,
        "path": str(dest_dir),
        "activated": bool(activate),
    }


def _find_installed_descriptor_paths(facets_dir: Path) -> list[Path]:
    if not facets_dir.is_dir():
        return []
    found: set[Path] = set()
    for p in facets_dir.glob("*/facet.yml"):
        if p.is_file():
            found.add(p)
    for p in facets_dir.glob("**/facet.yml"):
        if p.is_file():
            found.add(p)
    return sorted(found)


def _collect_installed_facet_ids(facets_dir: Path) -> tuple[set[str], list[str]]:
    ids: set[str] = set()
    parse_errors: list[str] = []
    for p in _find_installed_descriptor_paths(facets_dir):
        try:
            doc = load_yaml(p)
            fid, _ = validate_descriptor(doc, p)
            ids.add(fid)
        except Exception as e:
            parse_errors.append(f"descriptor.invalid: {p}: {e}")
    return ids, parse_errors


def runtime_status(project: Path) -> dict[str, Any]:
    cfg = normalize_project_config(project / ".pm" / "project.yml")
    lock = read_lock(project / ".pm" / "facet.lock.yml")

    active = list(cfg.get("active_facets", []))
    lock_ids = {
        str(rec.get("id", "")).strip()
        for rec in lock.get("facets", [])
        if isinstance(rec, dict) and str(rec.get("id", "")).strip()
    }
    installed_ids, parse_errors = _collect_installed_facet_ids(project / ".pm" / "facets")

    issues: list[dict[str, str]] = []

    for msg in parse_errors:
        issues.append(
            {
                "level": "error",
                "code": "descriptor.invalid",
                "message": msg,
                "remediation": "Fix or remove invalid descriptor under .pm/facets and re-run status/resolve --check.",
            }
        )

    for fid in sorted(set(active) - installed_ids):
        issues.append(
            {
                "level": "error",
                "code": "active_missing_installed",
                "message": f"Active facet has no installed descriptor: {fid}",
                "remediation": f"Install/link facet '{fid}' or deactivate it in .pm/project.yml.",
            }
        )

    for fid in sorted(lock_ids - installed_ids):
        issues.append(
            {
                "level": "error",
                "code": "lock_missing_installed",
                "message": f"Lockfile contains stale facet without installed descriptor: {fid}",
                "remediation": f"Reinstall '{fid}' or remove stale lock entry by lifecycle remove/install.",
            }
        )

    for fid in sorted(set(active) - lock_ids):
        issues.append(
            {
                "level": "error",
                "code": "active_missing_lock",
                "message": f"Active facet not pinned in lockfile: {fid}",
                "remediation": f"Reinstall/link '{fid}' to refresh lockfile pinning.",
            }
        )

    for fid in sorted(installed_ids - lock_ids):
        issues.append(
            {
                "level": "warning",
                "code": "installed_missing_lock",
                "message": f"Installed facet not present in lockfile: {fid}",
                "remediation": f"Run install/link for '{fid}' to create lock entry.",
            }
        )

    return {
        "ok": not any(i["level"] == "error" for i in issues),
        "active_facets": active,
        "installed_facets": sorted(installed_ids),
        "lock_facets": sorted(lock_ids),
        "issues": issues,
    }


def cmd_discover(args: argparse.Namespace) -> int:
    registry = Path(args.registry).resolve()
    if not registry.is_dir():
        err(f"registry dir not found: {registry}")
        return 2

    items: list[dict[str, str]] = []
    for p in sorted(registry.glob("**/facet.yml")):
        try:
            doc = load_yaml(p)
            fid, ver = validate_descriptor(doc, p)
            desc = str(doc.get("facet", {}).get("description", "")).strip()
            items.append({"id": fid, "version": ver, "description": desc, "path": str(p.parent)})
        except Exception:
            continue

    for it in items:
        print(f"{it['id']}\t{it['version']}\t{it['path']}")
    return 0


def cmd_install_like(args: argparse.Namespace, mode: str) -> int:
    project = Path(args.project).resolve()
    descriptor: Path
    source_uri = args.source_uri
    facet_id = args.facet_id
    if facet_id:
        try:
            reject_removed_legacy_id(facet_id)
        except Exception as e:
            err(str(e))
            return 1

    if args.source:
        source = Path(args.source).resolve()
        descriptor = source / "facet.yml" if source.is_dir() else source
        if not descriptor.is_file():
            err(f"facet descriptor not found: {descriptor}")
            return 2
    elif args.registry and facet_id:
        try:
            descriptor = find_registry_descriptor(Path(args.registry).resolve(), facet_id)
        except Exception as e:
            err(str(e))
            return 2
        if not source_uri:
            source_uri = str(descriptor.parent.resolve())
    else:
        err("provide either --source <facet-pack-dir|facet.yml> OR (--registry <dir> --facet-id <id>)")
        return 2

    try:
        out = install_from_descriptor(
            project,
            descriptor,
            mode=mode,
            activate=args.activate,
            source_uri=source_uri,
            allow_source_change=bool(args.allow_source_change),
            allow_digest_change=bool(args.allow_digest_change),
        )
    except Exception as e:
        err(str(e))
        return 1

    print(yaml.safe_dump(out, sort_keys=False, allow_unicode=True).strip())
    return 0


def cmd_activate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    cfg_path = project / ".pm" / "project.yml"
    facet_id = args.facet_id
    try:
        reject_removed_legacy_id(facet_id)
        cfg = normalize_project_config(cfg_path)
        if facet_id not in cfg["active_facets"]:
            cfg["active_facets"].append(facet_id)
        save_yaml(cfg_path, cfg)
    except Exception as e:
        err(str(e))
        return 1
    print(f"OK: activated {facet_id}")
    return 0


def cmd_deactivate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    cfg_path = project / ".pm" / "project.yml"
    facet_id = args.facet_id
    try:
        reject_removed_legacy_id(facet_id)
        cfg = normalize_project_config(cfg_path)
        cfg["active_facets"] = [x for x in cfg["active_facets"] if x != facet_id]
        save_yaml(cfg_path, cfg)
    except Exception as e:
        err(str(e))
        return 1
    print(f"OK: deactivated {facet_id}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    facet_id = args.facet_id
    try:
        reject_removed_legacy_id(facet_id)
    except Exception as e:
        err(str(e))
        return 1
    facet_dir = project / ".pm" / "facets" / facet_id
    if facet_dir.is_symlink() or facet_dir.is_file():
        facet_dir.unlink(missing_ok=True)
    elif facet_dir.is_dir():
        shutil.rmtree(facet_dir)

    lock_path = project / ".pm" / "facet.lock.yml"
    try:
        lock_data = read_lock(lock_path)
        remove_lock_entry(lock_data, facet_id)
        save_yaml(lock_path, lock_data)
    except Exception as e:
        err(str(e))
        return 1

    if args.deactivate:
        cfg_path = project / ".pm" / "project.yml"
        try:
            cfg = normalize_project_config(cfg_path)
            cfg["active_facets"] = [x for x in cfg["active_facets"] if x != facet_id]
            save_yaml(cfg_path, cfg)
        except Exception as e:
            err(str(e))
            return 1

    print(f"OK: removed {facet_id}")
    return 0


def cmd_list_installed(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    try:
        lock = read_lock(project / ".pm" / "facet.lock.yml")
    except Exception as e:
        err(str(e))
        return 1

    facets = lock.get("facets", []) if isinstance(lock, dict) else []
    if not isinstance(facets, list) or not facets:
        print("(none)")
        return 0

    for rec in sorted((r for r in facets if isinstance(r, dict)), key=lambda r: str(r.get("id", ""))):
        print(
            f"{rec.get('id','')}\t{rec.get('version','')}\t{rec.get('mode','')}\t"
            f"{rec.get('source','')}\t{rec.get('digest','')}"
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    try:
        status = runtime_status(project)
    except Exception as e:
        err(str(e))
        return 1

    print(yaml.safe_dump(status, sort_keys=False, allow_unicode=True).strip())
    return 0 if bool(status.get("ok")) else 1


def cmd_resolve(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    resolver = Path(__file__).resolve().parent / "facet_resolver.py"

    cmd = [sys.executable, str(resolver), str(project)]
    if args.check:
        cmd.append("--dry-run")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)

    if proc.returncode != 0:
        return proc.returncode

    if args.check:
        try:
            status = runtime_status(project)
        except Exception as e:
            err(str(e))
            return 1
        print(yaml.safe_dump(status, sort_keys=False, allow_unicode=True).strip())
        if not bool(status.get("ok")):
            err("resolve --check failed runtime consistency checks")
            return 1
        print("OK: resolve --check passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Facet lifecycle CLI (discover/install/link/activate/deactivate/remove/list-installed/status/resolve)"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Discover available facets in a registry directory")
    d.add_argument("--registry", required=True, help="Registry root directory containing facet packs")
    d.set_defaults(fn=cmd_discover)

    i = sub.add_parser("install", help="Install facet pack (copy mode)")
    i.add_argument("project", nargs="?", default=".", help="Project root")
    i.add_argument("--source", help="Facet source dir (contains facet.yml) or descriptor path")
    i.add_argument("--registry", help="Facet registry root")
    i.add_argument("--facet-id", help="Facet id to install from registry")
    i.add_argument("--source-uri", help="Optional source URI to record in lockfile")
    i.add_argument("--activate", action="store_true", help="Activate facet in .pm/project.yml")
    i.add_argument("--allow-source-change", action="store_true", help="Allow source provenance change for existing lock entry")
    i.add_argument("--allow-digest-change", action="store_true", help="Allow digest provenance change for existing lock entry")
    i.set_defaults(fn=lambda a: cmd_install_like(a, mode="copy"))

    l = sub.add_parser("link", help="Install facet pack as symlink")
    l.add_argument("project", nargs="?", default=".", help="Project root")
    l.add_argument("--source", help="Facet source dir (contains facet.yml) or descriptor path")
    l.add_argument("--registry", help="Facet registry root")
    l.add_argument("--facet-id", help="Facet id to link from registry")
    l.add_argument("--source-uri", help="Optional source URI to record in lockfile")
    l.add_argument("--activate", action="store_true", help="Activate facet in .pm/project.yml")
    l.add_argument("--allow-source-change", action="store_true", help="Allow source provenance change for existing lock entry")
    l.add_argument("--allow-digest-change", action="store_true", help="Allow digest provenance change for existing lock entry")
    l.set_defaults(fn=lambda a: cmd_install_like(a, mode="symlink"))

    a = sub.add_parser("activate", help="Activate installed facet")
    a.add_argument("project", nargs="?", default=".", help="Project root")
    a.add_argument("facet_id")
    a.set_defaults(fn=cmd_activate)

    da = sub.add_parser("deactivate", help="Deactivate facet")
    da.add_argument("project", nargs="?", default=".", help="Project root")
    da.add_argument("facet_id")
    da.set_defaults(fn=cmd_deactivate)

    rm = sub.add_parser("remove", help="Remove installed facet and lock entry")
    rm.add_argument("project", nargs="?", default=".", help="Project root")
    rm.add_argument("facet_id")
    rm.add_argument("--deactivate", action="store_true", help="Also remove from active_facets")
    rm.set_defaults(fn=cmd_remove)

    li = sub.add_parser("list-installed", help="List installed/pinned facets from lockfile")
    li.add_argument("project", nargs="?", default=".", help="Project root")
    li.set_defaults(fn=cmd_list_installed)

    st = sub.add_parser("status", help="Show facet runtime consistency status")
    st.add_argument("project", nargs="?", default=".", help="Project root")
    st.set_defaults(fn=cmd_status)

    rs = sub.add_parser("resolve", help="Run resolver; optionally check consistency")
    rs.add_argument("project", nargs="?", default=".", help="Project root")
    rs.add_argument("--check", action="store_true", help="Run resolver dry-run + consistency checks")
    rs.set_defaults(fn=cmd_resolve)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "facet_id") and args.facet_id and not FACET_ID_RE.fullmatch(str(args.facet_id)):
        err(f"invalid facet id: {args.facet_id!r}")
        return 2

    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
