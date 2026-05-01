# v1 Packaging Matrix and Consumer Contract

Status date: 2026-04-30
Task: T-105

## Purpose

Define the v1 packaging commitments and release acceptance contract before CI/release implementation changes.

## Packaging artifact matrix (v1)

| Artifact | Location/shape | Support tier | Consumer contract | Verification expectation |
|---|---|---|---|---|
| Source tarball | GitHub Release asset (`v*`) | Required | Must contain full source corresponding to the release tag commit. | Release asset exists; checksum published; tarball extracts cleanly. |
| Headers tarball (`core_v0.h`) | GitHub Release asset (`v*`) | Required | Must contain the canonical public C header used by consumers. | Release asset exists; checksum published; header path/content present. |
| SHA256 checksum file | GitHub Release asset (`v*`) | Required | Must include checksums for all required assets in this matrix. | Checksum file exists and entries match uploaded required assets. |
| Static library build artifact (`librtc_rs_core.a`) | Build output for release commit | Required | Must be buildable from release source on supported toolchain; consumers can statically link via documented flow. | Build + static consumer smoke command path passes for release commit. |
| Shared library build artifact (`librtc_rs_core.so`/platform equivalent) | Build output for release commit | Best-effort (v1) | Targeted for callback/interop validation and consumer convenience; temporary gaps do not block v1 release if required artifacts pass. | Shared callback smoke path attempted and evidence recorded when available. |
| Optional prebuilt platform binaries | Release assets by platform/arch | Best-effort (v1) | Convenience channel only; not required for v1 release acceptance. | If published, include checksum coverage and platform label clarity. |
| Packaging manifest (`packaging_manifest.json`) | Release artifact metadata in `dist/` | Required (v1 process) | Must describe required artifacts and optional prebuilt entries for deterministic consumer inspection. | Manifest exists and names required artifacts; optional prebuilt entries are explicit and non-blocking. |

## Release no-go criteria (v1)

A release is **no-go** when any required item below is missing or invalid:

1. Source tarball missing or checksum coverage missing.
2. Headers tarball missing or checksum coverage missing.
3. SHA256 checksum file missing or not covering required assets.
4. Required build/consumer verification evidence for static path absent or failing.

Best-effort artifacts (shared library convenience outputs / optional prebuilt binaries) do **not** block v1 release by themselves, but must be logged as follow-up if absent or failing.

Manifest generation is required for release-process validation, but optional prebuilt entries inside the manifest remain non-blocking.

## Consumer verification contract

For each release candidate tag:

1. Validate required release assets (source + headers + checksums) are present.
2. Validate checksum integrity for required assets.
3. Validate static consumer path against release commit/toolchain.
4. Record result evidence in task/release notes before cutover to published release communication.

## Out of scope (T-105 guard)

- CI/release workflow wiring for these checks (handled in T-106).
- New distribution channels or ABI/API expansion.

## Traceability

- Backlog: `.pm/backlog.md` (T-105)
- Task: `.pm/tasks/T-105.yml`
- Related baseline context: `docs/post-v0-roadmap.md`, `docs/v0-closeout.md`
