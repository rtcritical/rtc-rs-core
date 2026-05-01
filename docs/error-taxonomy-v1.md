# Error Taxonomy v1 (Status Mapping)

This document maps stable `rtc_status` codes to representative scenarios.

## Core status mapping

- `RTC_OK`: operation succeeded.
- `RTC_ERR_INVALID_ARG`: null pointers, invalid key/path payloads, foreign-context value usage, missing callback pointers.
- `RTC_ERR_TYPE`: type mismatch during get/assoc/update semantics or explicit callback/user type errors.
- `RTC_ERR_BOUNDS`: reserved for explicit bounds-specific checks (none newly introduced in this slice).
- `RTC_ERR_OOM`: reserved for allocation failures surfaced by runtime (not directly induced in deterministic tests).
- `RTC_ERR_OVERFLOW`: reserved for numeric overflow paths where surfaced.
- `RTC_ERR_STATE`: invalid runtime state (for example callback returns `RTC_OK` with null `out_next`).
- `RTC_ERR_INTERNAL`: panic/unwind catch or internal invariant conflict.

## Contract notes

- For callback-returned explicit errors, operations propagate callback status unchanged.
- Last-error message is context-scoped diagnostic and may remain unchanged for propagated callback errors.
- Context ownership mismatch is always `RTC_ERR_INVALID_ARG`.
