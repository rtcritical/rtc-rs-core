# Procedure - RTC GitHub Release Ops Runbook

## 1) Preflight go/no-go checks

1. Validate PM state and release task evidence before tagging.
2. Confirm default branch is green for required checks (`tests`, `consumer-smoke`, `policy`).
3. Confirm working tree is clean and release commit is immutable (no pending local drift).
4. Verify checkout depth/tag visibility requirements for release notes generation (`fetch-depth: 0` in release workflow).
5. Confirm packaging contract gate prerequisites are met (source tarball, headers tarball, SHA256SUMS).

No-go conditions:
- any required check red/pending,
- unresolved policy/runbook checklist items,
- tag collision or intent to mutate published tag.

## 2) Release execution

1. Cut a real `v*` tag from validated commit.
2. Push tag and verify workflow run starts.
3. Verify release workflow completion and asset publication.
4. Record release URL, workflow run URL/ID, and artifact checksum evidence in PM task notes.

## 3) Known failure modes and deterministic recovery

### A) Release-notes baseline/tag lookup failure
Symptom:
- release notes step fails around `git describe ... HEAD^` / no reachable tags.

Recovery:
1. Confirm repository/tag history visibility in workflow checkout.
2. Ensure release-notes script uses no-tag fallback path (merge log from `HEAD` when baseline tag missing).
3. Patch via PR if regression reappears; cut next patch tag after green checks.

### B) Packaging contract gate failure
Symptom:
- missing expected artifacts/checksums or contract mismatch.

Recovery:
1. Run `./scripts/check_packaging_contract.sh` locally and in CI.
2. Fix artifact build/publish logic in PR.
3. Re-run checks, then cut superseding patch tag.

### C) Tag ruleset/permission restriction
Symptom:
- tag push/release creation blocked by permission/ruleset.

Recovery:
1. Use least-privilege approved bypass actor path only.
2. Capture who/why/when in PM evidence.
3. Revoke/expire temporary bypass access after successful release.

### D) Stale/conflicting branch state before release prep
Symptom:
- release prep built from stale branch state or conflicted branch.

Recovery:
1. Sync from latest `origin/main`.
2. Re-run required checks and release preflight checklist.
3. Only then cut release tag.

## 4) Incident handling policy

1. Do not mutate published tags/releases.
2. For failed release attempts, patch in PR and cut next patch version.
3. Log incident summary (root cause, fix PR, replacement tag, run IDs, owner).

## 5) Evidence checklist (must capture)

- release tag and commit SHA
- release URL + release ID
- workflow run URL + run ID
- packaging contract gate output reference
- release notes generation evidence
- incident record (if any)
