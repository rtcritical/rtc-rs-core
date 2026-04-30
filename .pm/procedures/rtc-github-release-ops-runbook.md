# Procedure - RTC GitHub Release Ops Runbook

1. Validate PM state and release task evidence before tagging.
2. Verify checkout depth and tag/history requirements for release notes generation.
3. Cut a real `v*` tag and verify workflow completion + asset publication.
4. If release fails, capture root cause, patch in PR, and cut next patch tag.
5. Record release IDs, URLs, and workflow run IDs in task evidence.
