# Post-v0 roadmap

Status date: 2026-04-30

## Objective

Move from validated v0 baseline into predictable v0.x iteration with explicit priorities, acceptance gates, and low-risk sequencing.

## Milestone A — Consumer packaging ergonomics (v0.2 line)

### A1. Publish binary artifact matrix (optional channel)
- Keep canonical source+headers artifacts.
- Add optional prebuilt artifacts by platform/arch for faster consumer adoption.
- Gate: release workflow publishes matrix artifacts with checksums and manifest.
- Contract baseline: `docs/release-packaging-contract-v1.md`.

### A2. Consumer quickstart bundle
- Provide minimal examples for static + shared linking per platform.
- Gate: examples compile in CI smoke jobs.

### A3. ABI compatibility policy
- Define allowed vs breaking changes for `core_v0.h`.
- Gate: policy doc + CI guard for header signature drift (already partly covered by parity check).

## Milestone B — Reliability hardening (v0.2/v0.3)

### B1. Error taxonomy tightening
- Review and normalize `RTC_ERR_*` mapping for all edge paths.
- Gate: dedicated tests for each error contract path.

### B2. Callback contract stress tests
- Expand callback scenarios (null/foreign ctx/type mismatch/multiple mutation patterns).
- Gate: deterministic ABI surface test additions.

### B3. Fuzz/prop tests on core transforms
- Add lightweight property tests for roundtrip and invariants.
- Gate: property suite runs in CI policy or dedicated job.

## Milestone C — Delivery confidence and governance (v0.3)

### C1. Release runbook codification
- Consolidate release incident patterns and mitigation commands.
- Gate: `docs/release-runbook.md` + reproducible checklist.

### C2. API lifecycle notes
- Add deprecation/versioning notes for post-v0 evolution.
- Gate: CONTRIBUTING + docs/spec alignment.

---

## First execution PR after roadmap (recommended)

**PR1: `ci: add ABI compatibility policy guard`**

Why first:
- highest leverage for preventing accidental C-ABI breakage,
- low implementation risk,
- directly aligned with current FFI-focused quality bar.

Scope:
1. Add `docs/abi-compat-policy.md` (what constitutes breaking change in `core_v0.h`).
2. Add `scripts/check_abi_compat_policy.py`:
   - parse current header declarations,
   - enforce policy assertions (e.g., no removed exported symbols without explicit override path).
3. Wire guard into CI `policy` job.
4. Add changelog entry.

Acceptance gates:
- `cargo test --tests` pass,
- existing `check_abi_parity.py` pass,
- new compatibility policy check pass,
- CI job includes new check.

## Deferred (non-goal right now)

- Full multi-platform binary distribution matrix in one shot.
- API surface expansion beyond v0 contract.
- Broad refactors without direct quality/consumer benefit.
