# Task: Conformance harness bootstrap

- **Owner:** Nick + Clio
- **Status:** IN_PROGRESS
- **Goal:** Stand up parity harness skeleton for strict ABI + wrappers.
- **Acceptance:**
  - canonical vector loader
  - strict ABI runner stub
  - comparator skeleton + CI placeholder


## Progress
- Added canonical vector pack bootstrap (`harness/parity/vectors_v0.json`).
- Added parity loader tests and strict/comparator stubs (`tests/parity/*`).
- Added CI workflow placeholder (`.github/workflows/parity.yml`).


## Validation Notes
- `cargo test --tests` passes for harness bootstrap.
- Full `cargo test` currently fails in this runtime due missing `rustdoc` executable for doc-tests.
