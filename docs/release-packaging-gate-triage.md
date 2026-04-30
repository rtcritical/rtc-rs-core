# Packaging Gate Failure Triage (T-106)

Status date: 2026-04-30

## Gate scope

Required v1 checks:
- source tarball exists and is non-empty
- headers tarball exists and is non-empty
- SHA256SUMS exists and includes required tarballs
- static library build artifact exists (`target/release/librtc_rs_core.a`)
- release notes generation succeeds

## Standard local reproduction

```bash
./scripts/check_packaging_contract.sh
./scripts/prepare_release_notes.py
```

## Common failures and fixes

1. `missing librtc_rs_core.a`
- Cause: release build did not complete or profile mismatch.
- Fix: rerun `cargo build --release`; confirm `target/release/librtc_rs_core.a` exists.

2. `missing/empty source or headers tarball`
- Cause: tar command failure or path drift.
- Fix: verify `include/core_v0.h` exists; rerun packaging script.

3. `SHA256SUMS missing required entries`
- Cause: checksum command executed before tarball creation or wrong glob.
- Fix: regenerate tarballs first, then rerun checksum step.

4. `prepare_release_notes.py` failure
- Cause: tag/history depth, category mapping, or PR metadata issue.
- Fix: ensure full git history in CI checkout (`fetch-depth: 0`), then rerun release-notes step.

## No-go decision rule

Do not cut/publish release while any required packaging gate is red.
