# Policy - RTC GitHub Release Ops

- Release tags (`v*`) must be reproducible from git state and workflow evidence.
- Release notes generation must be deterministic and validated in CI.
- Tag ruleset bypass, when required, must be least-privilege and explicitly documented.
- Failed release attempts should be superseded by a new tag/version; avoid mutating published tags.
