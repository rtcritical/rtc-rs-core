# Task: Conformance harness bootstrap

- **Owner:** Nick + Clio
- **Status:** DONE
- **Goal:** Stand up parity harness skeleton for strict ABI + wrappers.
- **Acceptance:**
  - canonical vector loader
  - strict ABI runner stub
  - comparator skeleton + CI placeholder


## Progress
- Added canonical vector pack bootstrap (`harness/parity/vectors_v0.json`).
- Added parity loader tests and strict/comparator stubs (`tests/parity/*`).
- Added CI workflow placeholder (`.github/workflows/parity.yml`).
- Replaced parity stubs with active runner/comparator tests.

## Validation Notes
- `cargo test --tests` passes for harness bootstrap and active parity checks.
- Full `cargo test` may fail in runtimes missing `rustdoc` for doc-tests.
