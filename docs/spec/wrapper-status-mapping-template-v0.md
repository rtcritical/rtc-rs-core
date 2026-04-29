# Wrapper Status Mapping Template (v0)

## Purpose
Define a required per-wrapper mapping from strict C ABI statuses to host-language error/result categories.

## Required Mapping Table
Fill this for each wrapper package.

| Strict ABI Status | Wrapper Category | Wrapper Type/Class | Notes |
|---|---|---|---|
| RTC_OK | success | <type> | |
| RTC_ERR_INVALID_ARG | argument_error | <type> | |
| RTC_ERR_TYPE | type_error | <type> | |
| RTC_ERR_BOUNDS | bounds_error | <type> | |
| RTC_ERR_OOM | resource_error | <type> | |
| RTC_ERR_OVERFLOW | overflow_error | <type> | |
| RTC_ERR_STATE | state_error | <type> | |
| RTC_ERR_INTERNAL | internal_error | <type> | |

## Required Behavioral Rules
1. Non-OK statuses MUST NOT be silently swallowed.
2. `rtc_last_error_message(ctx)` SHOULD be attached to wrapper error objects when available.
3. Missing-path read semantics MUST remain `nil-equivalent + success`.
4. `update/update_in` missing target MUST apply updater to nil-equivalent.

## Wrapper Metadata (fill)
- Wrapper name:
- Language/runtime:
- Version:
- Maintainer:
- Last parity run:
