# Procedure - PM Operations (Kernel Baseline)

## Purpose
Define the minimal kernel-owned operator baseline for day-to-day PM execution so projects remain recoverable and consistent even when no facet overlays are active.

## Baseline scope (kernel-owned)
This baseline intentionally includes only:
- mandatory PM input preflight
- minimum daily/weekly loop skeleton
- authority boundaries
- validation + commit-readiness checks
- escalation triggers
- core lane/policy references

Operational governance variants and richer domain runbooks should be delivered through facet overlays.

## Required inputs before operating
0. `.pm/generated/pm-runtime-brief.yml` (authoritative, deterministic runtime contract)
1. `.pm/charter.md`
2. `.pm/goals.md`
3. `.pm/scope.md`
4. `.pm/backlog.md`
5. Latest `.pm/status/` entry
6. Relevant `.pm/decisions/` ADRs
7. Applicable policies/procedures under `.pm/policies/` and `.pm/procedures/`

If required inputs are missing or contradictory, stop and raise blocker.

## Deterministic facet runtime brief (required)
- Generate with: `python3 scripts/generate_pm_runtime_brief.py <project-path>`
- Validate freshness/contract with: `python3 scripts/check_pm_runtime_brief.py <project-path>`
- Treat the brief as authoritative for:
  - active facet set and lock-pinned provenance
  - ordered facet overlay policy/procedure pre-reads
  - required runtime checks
- Kernel procedure text must not hardcode specific facet IDs; use the runtime brief instead.

## Core policy/SOP references (baseline)
- `docs/policy/PM_DEFAULT_ORCHESTRATION_POLICY.md`
- `docs/sop/PM_EXECUTION_LANE_SOP.md`
- `docs/spec/PM_TOGGLE_ENFORCEMENT_CONTRACT.md` (strict mode + toggles)
- `docs/spec/PM_KERNEL_FACET_ARCHITECTURE_MANUAL_V1.md`
- `docs/policy/PM_POLICY_PROCEDURE_PLACEMENT_MODEL_V1.md`
- `docs/spec/PM_RUNTIME_BRIEF_CONTRACT_V1_DRAFT.md`

## Daily baseline loop
0. **Task-boundary clean check (required)**:
   - before starting a new task slice, workspace must be clean (`git status --short` empty)
   - before committing a task slice, no unstaged/untracked drift is allowed outside commit scope
1. **Ingest**: capture new intake into `.pm/inbox/raw/` with source refs.
2. **Triage**: classify and link to epic/task where possible.
3. **Plan update**: update backlog status/ownership/dependencies.
4. **Decision hygiene**: log consequential tradeoffs in ADR/open-question artifacts.
5. **Status update**: update `.pm/status/` with done / in-progress / blockers / next.
6. **Validation**: run `python3 scripts/validate_pm.py <project-path>`.
7. **Gap check (required pre-commit)**:
   - compare commit scope vs charter/goals/scope/backlog/procedures
   - either close missing validation gaps or taskize them before commit
8. **Post-commit clean check (required)**:
   - immediately after commit, confirm workspace returns to clean state before starting next task
9. **Non-lossy engineering analysis capture (expected default for any task when analysis exists)**:
   - if substantive engineering analysis was produced at any stage (intake, planning, design, implementation, review, defer/park/close), the default is to persist an analysis artifact within the same task slice.
   - artifact format is flexible: engineering analysis note, tradeoff memo, or ADR/decision record when an actual decision was made.
   - summaries alone are usually insufficient; capture enough detail (context, alternatives, tradeoffs, examples, false positives/negatives when relevant, and trigger criteria) to resume without re-deriving prior reasoning.
   - link the artifact from task refs (use `context_refs` and/or `evidence_refs`; include `decision_refs` when the artifact is a decision/ADR).
   - quick-fix exception: when no substantive analysis exists, note `analysis_depth=none` (or equivalent) in task notes/status.
   - this is a strong operating norm, not a hard checker gate by default.

## Weekly baseline loop
- Review scope drift, blockers, stale in-progress tasks, and policy/procedure compliance.

## Authority matrix (baseline)

### Agent may update without pre-approval
- `.pm/backlog.md` (status/detail updates, additive tasks)
- `.pm/status/*.md`
- `.pm/decisions/*.md` (drafting/logging decisions already made)
- `.pm/inbox/raw/*` (capture only; no destructive edits)

### Agent must request approval first
- `.pm/charter.md` changes
- `.pm/goals.md` priority shifts altering declared priority intent (P0-P4)
- `.pm/scope.md` boundary changes
- `.pm/stakeholders.yml` decision-right changes
- destructive/irreversible operations

## Escalation triggers
- conflicting directives across charter/goals/scope
- tradeoffs affecting delivery dates, risk posture, approval model
- ambiguous owner/decision-right for blocked item
- requests conflicting with policy/procedure guardrails

## Facet overlay extensions (composition hooks)
Facet overlays MAY extend the baseline with domain-specific policy/procedure content, such as:
- governance operating rules
- comms procedures
- domain runbooks/checklists

Overlay sources should live under facet paths (for example `.pm/facets/<facet-id>/policies/*.md` and `.pm/facets/<facet-id>/procedures/*.md`) and remain subordinate to kernel invariants.

## Facet overlay references
- Resolve from `.pm/generated/pm-runtime-brief.yml` (`facet_overlay_required_reads` + `active_facets[].required_reads`).

## Related references
- `docs/spec/PM_KERNEL_BASELINE_ALLOWLIST_V1.md`
- `docs/spec/PM_KERNEL_FACET_OWNERSHIP_MATRIX_V1.md`
- `docs/policy/PM_POLICY_PROCEDURE_PLACEMENT_MODEL_V1.md`
- `docs/spec/PM_RUNTIME_BRIEF_CONTRACT_V1_DRAFT.md`
