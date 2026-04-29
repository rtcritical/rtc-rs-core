# PM Execution Readiness Policy (V1)

## Purpose
Define the default execution-readiness contract for PM task/doc updates so implementation can proceed with engineering-grade clarity, traceability, and rollback awareness.

## Default-on position
`pm.execution.readiness` is default active for PM-managed projects because incomplete execution context is a recurring source of schedule slip, rework, and unsafe changes. This policy raises baseline delivery quality while remaining lifecycle-toggleable.

## Readiness contract
A task/doc is execution-ready only when it includes all required readiness fields:

- objective
- scope
- constraints
- assumptions
- decision rationale
- alternatives considered
- dependencies
- acceptance criteria
- validation plan
- rollback/risk
- open questions

## Enforcement
When `require_task_execution_readiness=true`, the toggle checker must fail closed if any required field is missing or empty and return actionable diagnostics naming exact missing fields and remediation targets.

## Boundaries
- Kernel ownership, resolver behavior, and lifecycle semantics remain unchanged.
- This facet only contributes toggle-registry/checker + policy/procedure content.
- Project operators may deactivate without uninstalling when intentionally relaxing readiness strictness.

## Lifecycle controls
- Deactivate (keep installed):
  - `python3 .pm/scripts/facet_lifecycle.py deactivate <project-path> pm.execution.readiness`
- Re-activate:
  - `python3 .pm/scripts/facet_lifecycle.py activate <project-path> pm.execution.readiness`
- Optional full remove:
  - `python3 .pm/scripts/facet_lifecycle.py remove <project-path> pm.execution.readiness --deactivate`
