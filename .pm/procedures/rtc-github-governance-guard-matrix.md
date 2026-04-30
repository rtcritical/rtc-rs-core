# RTC GitHub Governance Guard Matrix (Local vs CI)

## Purpose
Map governance controls to local hooks and CI enforcement so behavior is predictable and bypasses are explicit.

## Guard parity matrix

| Guard | Local pre-commit | CI policy job | Notes |
|---|---|---|---|
| PM schema/content validation (`validate_pm.py`) | Yes | Yes | Baseline PM integrity check. |
| PM toggles (`check_pm_toggles.py`) | Yes | Yes | Includes readiness/open-question enforcement. |
| PM task binding (`check_pm_task_binding.py`) | Yes (staged scope) | Yes (base..head range) | CI is authoritative for full PR range. |
| Lane compliance (`check_pm_lane_compliance.py`) | Yes | Indirect via PM validate suite policy expectations | Local fast feedback. |
| Markdown ASCII guard | Yes | Indirect via PM validate expectations | Prevents formatting drift. |
| Changelog policy (`check_changelog.sh`) | No | Yes | CI-only merge gate. |
| ABI parity policy (`check_abi_parity.py`) | No | Yes | CI-only merge gate. |
| ABI compatibility policy (`check_abi_compat_policy.py`) | No | Yes | CI-only merge gate. |
| Packaging contract gate (`check_packaging_contract.sh`) | No | Yes | CI-only merge gate. |
| Release-notes generation gate (`prepare_release_notes.py`) | No | Yes | CI detects release-note regressions early. |
| Facet presence checks (`run_facet_checks.py`) | Yes | Indirect via PM validate suite | Local guard for facet completeness. |

## Bypass policy (minimally permissive)

1. **Default stance:** no bypass for required CI checks.
2. **Emergency-only local bypass:** may skip local hook checks only to unblock urgent fix authoring, but merge remains blocked until CI passes.
3. **Approval requirement:** any emergency bypass must be explicitly approved by Nick and logged in PM evidence.
4. **Expiry/cleanup:** bypass condition expires after the emergency PR is merged/closed; restore normal hook/config immediately.
5. **Audit record required:** include who approved, why, scope, start/end timestamp, and restoration confirmation.

## Drift vectors and controls

- Drift vector: local hook script changed without CI parity update.
  - Control: require matrix review when `.githooks/pre-commit` or `.github/workflows/ci.yml` changes.
- Drift vector: CI-only guards surprise contributors late.
  - Control: document CI-only guards explicitly in this matrix and runbook.
- Drift vector: silent emergency bypass persistence.
  - Control: mandatory expiry + restoration evidence in PM task notes.

## Proof sample commands

Local:
- `python3 .pm/scripts/validate_pm.py .`
- `python3 .pm/scripts/check_pm_toggles.py .`
- `python3 .pm/scripts/check_pm_task_binding.py .`

CI policy equivalents:
- `python3 .pm/scripts/validate_pm.py .`
- `python3 .pm/scripts/check_pm_toggles.py .`
- `python3 .pm/scripts/check_pm_task_binding.py . --base <base> --head <head>`
- `./scripts/check_changelog.sh`
- `./scripts/check_abi_parity.py`
- `./scripts/check_abi_compat_policy.py`
- `./scripts/check_packaging_contract.sh`
- `./scripts/prepare_release_notes.py`
