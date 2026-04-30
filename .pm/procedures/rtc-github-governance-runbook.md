# Procedure - RTC GitHub Governance Runbook

1. Validate PM baseline and task binding before repository governance changes.
2. Verify CI job names align with required check contexts.
3. Verify release workflow behavior with a real `v*` tag test in controlled flow.
4. If tag ruleset restrictions block release tags, use least-privilege bypass actor policy.
5. Use `github-ops` skill for GitHub API mutations; record evidence refs in PM tasks.
