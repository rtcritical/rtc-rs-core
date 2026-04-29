# PM Execution Readiness Runbook (V1)

## Purpose
Operational steps for satisfying and troubleshooting execution-readiness checks before implementation runs.

## When to run
- Before moving a task from planning into implementation-ready execution.
- During strict-mode checks when `require_task_execution_readiness` is enabled.
- When check outputs report missing readiness fields.

## Required readiness fields
Ensure the target task/doc includes populated entries for:

1. objective
2. scope
3. constraints
4. assumptions
5. decision rationale
6. alternatives considered
7. dependencies
8. acceptance criteria
9. validation plan
10. rollback/risk
11. open questions

## Procedure
1. Identify the active task file(s) under `.pm/tasks/` tied to staged implementation changes.
2. Add/update a structured `execution_readiness` object in each impacted task with all required fields.
3. Run toggle enforcement:
   - `python3 .pm/scripts/check_pm_toggles.py <project-path>`
4. If failing, remediate missing fields listed in diagnostics and re-run checks.
5. Run PM gates (`validate_pm`, facet checks, and suite gates) before merge.

## Typical remediation
- Missing decision context -> add `decision_rationale` plus `alternatives_considered`.
- Missing validation detail -> define concrete `validation_plan` steps and expected success criteria.
- Missing safety fallback -> document `rollback_risk` including rollback trigger and blast radius.

## Lifecycle opt-out (temporary)
When intentionally operating outside strict readiness requirements:
- Deactivate:
  - `python3 .pm/scripts/facet_lifecycle.py deactivate <project-path> pm.execution.readiness`
- Re-activate after exception closes:
  - `python3 .pm/scripts/facet_lifecycle.py activate <project-path> pm.execution.readiness`
