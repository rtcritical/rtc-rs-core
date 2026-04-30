# Procedure - RTC GitHub Governance Runbook

1. Validate PM baseline and task binding before repository governance changes.
2. Verify CI job names align with required check contexts.
3. Verify release workflow behavior with a real `v*` tag test in controlled flow.
4. If tag ruleset restrictions block release tags, use least-privilege bypass actor policy.
5. Use `github-ops` skill for GitHub API mutations; record evidence refs in PM tasks.

## Standard execution loop (momentum + CI)

1. Sync delivery branch from latest `origin/main` at task start.
2. Execute one PM task slice with bounded scope.
3. Run required local validation and PM guards.
4. Push delivery branch and wait for required GitHub checks.
5. If checks are green, continue to next task slice on same delivery branch.
6. If checks fail, stop progression and remediate before continuing.

## PR strategy

- Default: one PR per epic/delivery branch (not one PR per task).
- Keep task-level commits and PM evidence updates for auditability.
- Split into smaller PRs only when risk/size/conflict profile justifies it.

## Merge protocol

- Default: Clio may merge once required checks pass and no explicit hold is present.
- On merge, immediately fast-forward local `main` and re-seed the next delivery branch from updated `origin/main`.
