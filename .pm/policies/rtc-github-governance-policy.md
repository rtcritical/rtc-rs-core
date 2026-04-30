# Policy - RTC GitHub Governance

- PM-enabled repos must enforce protected-default-branch behavior.
- Required check contexts must be explicit and stable.
- Release workflows must be auditable and reproducible.
- External GitHub mutations must run through approved ops tooling.

## Delivery flow policy (epic-branch + task gates)

- Default delivery unit is an epic branch (`epic/<epic-id>-<slug>` or equivalent project prefix).
- PM task completion does not require one PR per task; task traceability is required at commit/task artifact level.
- CI must run on every push to active delivery branches and PRs.
- Task-to-task progression on an active delivery branch requires green required checks (or explicit human override).
- Long-lived delivery branches must sync with `origin/main` at task boundaries (rebase preferred) before continuing.

## Merge authority

- Unless explicitly held by Nick, Clio may merge PRs when all required checks are green and branch protection is satisfied.
- Human approval remains required for exceptional/high-risk changes (for example: destructive repository operations, security posture downgrades, or emergency release-path overrides).

## Emergency bypass policy

- Local-hook bypass is emergency-only and does not waive required CI checks.
- Any bypass event must be explicitly approved by Nick, time-bounded, and recorded with restoration evidence.
