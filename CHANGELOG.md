# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Release-notes prep guardrail now fails when merge commits exist but categorization would produce zero assigned entries, preventing silent empty-note regressions.
- Release notes prep now categorizes merged PRs semantically by GitHub labels (using API lookup), with heuristic fallback when labels are unavailable.
- Label-category-based release notes prep script (`scripts/prepare_release_notes.py`) wired into release workflow via `body_path`.
- Shared-library callback consumer smoke harness (`harness/consumer_smoke_callback.c`) covering callback-based mutation flow from a C caller.
- ABI parity policy script (`scripts/check_abi_parity.py`) to fail CI when C header declarations and Rust `extern "C"` exports drift.
- Consumer C smoke harness (`harness/consumer_smoke.c`) to validate real C caller linkage and basic ABI roundtrip behavior in CI.
- ABI safety documentation clarifying context ownership invariants for mutating `rtc_n*` operations.
- Header-level callback contract note requiring `out_next` values to be owned by the provided `rtc_ctx` when returning `RTC_OK`.

### Changed
- C header operation notes now document read/mutation behavior, out-parameter clearing expectations, and ownership consistency requirements.

### Fixed
- Added ABI test coverage for callback lifecycle safety: `rtc_nupdate` now explicitly tested to reject callback-produced values from a different context.
