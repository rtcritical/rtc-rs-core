# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Shared-library callback consumer smoke harness (`harness/consumer_smoke_callback.c`) covering callback-based mutation flow from a C caller.
- ABI parity policy script (`scripts/check_abi_parity.py`) to fail CI when C header declarations and Rust `extern "C"` exports drift.
- Consumer C smoke harness (`harness/consumer_smoke.c`) to validate real C caller linkage and basic ABI roundtrip behavior in CI.
- ABI safety documentation clarifying context ownership invariants for mutating `rtc_n*` operations.
- Header-level callback contract note requiring `out_next` values to be owned by the provided `rtc_ctx` when returning `RTC_OK`.

### Changed
- C header operation notes now document read/mutation behavior, out-parameter clearing expectations, and ownership consistency requirements.

### Fixed
- 
