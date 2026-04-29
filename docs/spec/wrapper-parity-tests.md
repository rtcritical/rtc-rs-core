# Wrapper Parity Test Spec (v0 Draft)

## Purpose
Ensure ergonomic language wrappers preserve the exact semantics of the canonical strict C ABI.

## Scope
- Canonical ABI: strict `*_ex` functions + status codes
- Wrapper surfaces: language-idiomatic APIs (exceptions/results/nil-friendly helpers)
- Out of scope: wrapper-only convenience features that do not alter core semantics

## Parity Rule
For any logical operation, wrapper behavior MUST map to the same semantic outcome as strict ABI behavior.

---

## Group 1: Missing-path semantics parity

### Cases
1. `get/get_in` missing key/path
   - Strict ABI expectation: `RTC_OK`, output `nil`
   - Wrapper expectation: language-level nil/none/null equivalent without hard error

2. `nassoc_in` with missing intermediate path
   - Strict ABI expectation: path creation by default, `RTC_OK`
   - Wrapper expectation: same effective path-creation result

3. `update/nupdate_in` missing target
   - Strict ABI expectation: updater receives `nil`; success path returns `RTC_OK` when updater succeeds
   - Wrapper expectation: updater callback receives language nil equivalent

---

## Group 2: Type-conflict/status parity

### Cases
1. `get_in` traverses through non-container value
   - Strict ABI expectation: `RTC_ERR_TYPE`
   - Wrapper expectation: mapped deterministic typed error/result

2. `nassoc_in` path creation blocked by type conflict
   - Strict ABI expectation: `RTC_ERR_TYPE`
   - Wrapper expectation: equivalent typed failure

3. Invalid args (null handles / malformed key-path descriptors in FFI)
   - Strict ABI expectation: `RTC_ERR_INVALID_ARG`
   - Wrapper expectation: deterministic argument error mapping

---

## Group 3: Numeric/overflow boundary parity

### Cases
1. `i64` min/max roundtrip through wrappers
   - Strict ABI expectation: value preserved, `RTC_OK`
   - Wrapper expectation: same value preserved

2. Overflow/coercion failure paths
   - Strict ABI expectation: `RTC_ERR_OVERFLOW`
   - Wrapper expectation: explicit overflow error mapping (not silent truncation)

3. Length/count boundary handling (`uint64_t` ABI fields)
   - Strict ABI expectation: deterministic error on invalid conversions/limits
   - Wrapper expectation: same error category surfaced

---

## Group 4: Error propagation parity

### Cases
1. Strict status-to-wrapper mapping table is complete
   - `RTC_ERR_INVALID_ARG`, `RTC_ERR_TYPE`, `RTC_ERR_BOUNDS`, `RTC_ERR_OOM`, `RTC_ERR_OVERFLOW`, `RTC_ERR_STATE`, `RTC_ERR_INTERNAL`

2. Error message propagation
   - Wrapper retrieves/propagates `rtc_last_error_message(ctx)` where available
   - No wrapper swallows non-OK ABI status without explicit documented conversion

3. Determinism
   - Same input shape + operation MUST yield same wrapper-visible category across runs

---

## Conformance Harness Requirements

1. Shared test vectors:
   - One canonical set of JSON-compatible nested structures and operation scripts
2. Dual execution mode:
   - Execute each vector via strict ABI harness and via wrapper API harness
3. Result comparator:
   - Compare semantic outcomes: value shape, nil/missing behavior, error category
4. CI gate:
   - Wrapper release is blocked if parity suite fails

---

## Initial Wrapper Targets (v0)
- Python wrapper
- Java/JNI wrapper

Additional wrappers (Node/Go/etc.) SHOULD adopt the same parity harness contract.
