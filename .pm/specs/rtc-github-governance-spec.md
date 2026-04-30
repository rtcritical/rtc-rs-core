# RTC GitHub Governance Spec

## Objective
Define enforceable GitHub governance expectations for PM-managed repositories.

## Scope
- Branch protection expectations for default branch.
- Tag/release governance expectations.
- Required CI context naming expectations.
- Separation of facet contracts vs external API mutation tooling.
- Delivery model expectations for epic branches with task-level CI gating.
- Merge authority defaults for agent-driven PR completion under green required checks.

## Out of Scope
- Executing GitHub API writes directly.
- Managing credentials/tokens in PM files.

## Delivery model (normative)

- A PM task is the minimum traceability unit; a PR may contain multiple tasks when scope remains coherent.
- Delivery branches must receive CI validation on each push before subsequent task progression.
- Delivery branches should be rebased/synced with `origin/main` at task boundaries to reduce late conflict accumulation.
