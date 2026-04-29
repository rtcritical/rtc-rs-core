#!/usr/bin/env python3
"""Fail if policy/procedure placement violates kernel-vs-facet model.

T-090 guardrail:
- kernel paths keep only approved baseline artifacts
- additional policy/procedure behavior docs must be facet-owned
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]

KERNEL_POLICY_ALLOWLIST = {
    "docs/policy/PM_DEFAULT_ORCHESTRATION_POLICY.md",
    "docs/policy/PM_RUNTIME_STRICT_AUTHORITY_POLICY_V1_DRAFT.md",
    "docs/policy/PM_POLICY_PROCEDURE_PLACEMENT_MODEL_V1.md",
    # Transitional kernel-path policies pending dedicated migration slices.
    "docs/policy/TEST_SCRIPT_HEADER_CONTRACT.md",
    "docs/policy/PM_CORE_GOVERNANCE_CHANGE_CONTROL_POLICY_V1_DRAFT.md",
    "docs/policy/PM_CONTROL_LOOP_RUNTIME_POLICY_V1_DRAFT.md",
    "docs/policy/AGENT_INTAKE_POLICY.md",
    "docs/policy/PM_TEMPLATE_COMPATIBILITY_POLICY.md",
}

KERNEL_PROCEDURE_ALLOWLIST = {
    ".pm/procedures/pm-operations.md",
}

SKIP_DIRS = {".git", ".venv", "__pycache__"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        yield rel


def main() -> int:
    violations: list[str] = []

    for rel in iter_files(REPO):
        if rel.startswith("docs/policy/") and rel.endswith(".md"):
            if rel not in KERNEL_POLICY_ALLOWLIST:
                violations.append(
                    f"{rel}: policy doc in kernel path is not allowlisted; move to facet overlay or justify via placement decision"
                )
        if rel.startswith(".pm/procedures/") and rel.endswith(".md"):
            if rel in {".pm/procedures/README.md"}:
                # Procedures index is kernel-owned for discoverability.
                continue
            if rel not in KERNEL_PROCEDURE_ALLOWLIST:
                violations.append(
                    f"{rel}: procedure doc in kernel path is not allowlisted; move to facet overlay or justify via placement decision"
                )

    if violations:
        print("ERROR: policy/procedure placement violations detected:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("OK: policy/procedure placement guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
