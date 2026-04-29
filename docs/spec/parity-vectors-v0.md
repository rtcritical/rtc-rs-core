# Parity Vectors v0 (Canonical)

## Purpose
Define a canonical vector set that every wrapper and strict ABI harness MUST execute identically.

## Conventions
- Missing reads return nil-equivalent + success.
- `assoc_in` creates missing path segments.
- `update`/`update_in` apply updater to nil on missing target.
- Object/map ordering is unspecified and MUST NOT be used as an assertion key.
- Assertions compare semantic value shape/content and status category.

---

## Vector 01 — Missing top-level key
**Input root**
```json
{"a":1}
```
**Op**: `get_in(["missing"])`
**Expected**: `RTC_OK`, result `nil`

## Vector 02 — Missing nested path
**Input root**
```json
{"a":{"b":1}}
```
**Op**: `get_in(["a","z"])`
**Expected**: `RTC_OK`, result `nil`

## Vector 03 — `assoc_in` path creation
**Input root**
```json
{}
```
**Op**: `assoc_in(["cfg","http","port"], 8080)`
**Expected**: `RTC_OK`, result contains `{ "cfg": { "http": { "port": 8080 } } }`

## Vector 04 — `update_in` missing target gets nil
**Input root**
```json
{}
```
**Op**: `update_in(["x"], fn_nil_to_1)` where updater maps nil->1
**Expected**: `RTC_OK`, result `{ "x": 1 }`

## Vector 05 — Type conflict on traversal
**Input root**
```json
{"a":1}
```
**Op**: `get_in(["a","b"])`
**Expected**: `RTC_ERR_TYPE`

## Vector 06 — `assoc_in` type conflict
**Input root**
```json
{"a":1}
```
**Op**: `assoc_in(["a","b"], 2)`
**Expected**: `RTC_ERR_TYPE`

## Vector 07 — Vector index read hit
**Input root**
```json
{"arr":[7,8,9]}
```
**Op**: `get_in(["arr",1])`
**Expected**: `RTC_OK`, result `8`

## Vector 08 — Vector index bounds miss behavior
**Input root**
```json
{"arr":[7,8,9]}
```
**Op**: `get_in(["arr",5])`
**Expected**: `RTC_OK`, result `nil`

## Vector 09 — Invalid arg (malformed path descriptor)
**Input root**: any
**Op**: strict ABI call with invalid path/key descriptor
**Expected**: `RTC_ERR_INVALID_ARG`

## Vector 10 — Numeric boundary i64 max
**Input root**
```json
{"n":9223372036854775807}
```
**Op**: `get_in(["n"])` roundtrip via wrapper
**Expected**: `RTC_OK`, exact value preserved

## Vector 11 — Numeric boundary i64 min
**Input root**
```json
{"n":-9223372036854775808}
```
**Op**: `get_in(["n"])` roundtrip via wrapper
**Expected**: `RTC_OK`, exact value preserved

## Vector 12 — Overflow mapping
**Input root**: wrapper-specific setup
**Op**: force out-of-range conversion into i64/f64 boundary API
**Expected**: `RTC_ERR_OVERFLOW` mapped explicitly (no silent truncation)

---

## Wrapper Mapping Requirements
Each wrapper MUST publish a mapping table:
- strict status -> wrapper error/result category
- nil-equivalent type in host language
- updater callback failure mapping behavior

## Comparator Rules
Harness comparator MUST verify:
1. Status category parity
2. Semantic value parity
3. Nil/missing parity
4. Deterministic error category parity

## CI Gate
Wrapper CI MUST fail if any canonical vector diverges from strict ABI harness output.
