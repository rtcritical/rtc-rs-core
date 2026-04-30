# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- ABI safety documentation clarifying context ownership invariants for mutating `rtc_n*` operations.
- Header-level callback contract note requiring `out_next` values to be owned by the provided `rtc_ctx` when returning `RTC_OK`.

### Changed
- C header operation notes now document read/mutation behavior, out-parameter clearing expectations, and ownership consistency requirements.

### Fixed
- 
