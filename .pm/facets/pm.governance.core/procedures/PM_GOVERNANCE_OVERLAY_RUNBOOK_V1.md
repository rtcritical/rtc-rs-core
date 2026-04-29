# PM Governance Overlay Runbook (V1)

## Purpose
Facet-owned governance runbook that composes with kernel baseline PM operations.

## When to use
Use this runbook for governance-sensitive PM slices (policy/procedure/boundary changes) after kernel baseline preflight is satisfied.

## Overlay procedure
1. Confirm kernel baseline preflight from `.pm/procedures/pm-operations.md`.
2. Identify governance-sensitive files and required approval points.
3. Ensure open-question artifact exists when required by active toggles.
4. Run validation gates (`check_pm_toggles`, `validate_pm`, non-agent tests as needed).
5. Attach evidence refs in task closure metadata.

## Exit criteria
- Governance change has explicit decision trace.
- Validation and evidence requirements pass.
- Task/backlog views are re-rendered and consistent.
