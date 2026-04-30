# rtc-rs-core

RTCritical’s universal hierarchical data model library.

- Created in Rust
- Strict C ABI shim for cross-language / cross-platform use
- Companion JSON package strategy
- Clojure-inspired for simplicity and usability

## Status

**v0 complete**

## Implemented API surface

### 1) Rust API module (`src/api.rs`)

Constructors / values:
- `nil`, `b`, `i`, `f`, `st`
- `v!`, `s!`, `m!`
- `v_from`, `s_from`, `m_from`

Map helpers:
- `keys`
- `vals`

Operations:
- Reads: `get`, `get_in`
- Mutable updates (`n*`): `nassoc`, `nassoc_in`, `nupdate`, `nupdate_in`

### 2) C ABI (`include/core_v0.h`)

Context / errors:
- `rtc_ctx_new`, `rtc_ctx_free`
- `rtc_last_error_code`, `rtc_last_error_message`

Constructors / inspect:
- `rtc_nil`, `rtc_bool`, `rtc_i64`, `rtc_f64`, `rtc_string`
- `rtc_kind_of`, `rtc_as_bool`, `rtc_as_i64`, `rtc_as_f64`, `rtc_as_string`

Operations:
- Reads: `rtc_get`, `rtc_get_in`
- Mutable updates (`n*`): `rtc_nassoc`, `rtc_nassoc_in`, `rtc_nupdate`, `rtc_nupdate_in`

## Source of truth
- ADR and specs under `docs/`
- PM workflow under `.pm/`

## Tests

```bash
cargo test --tests
```

## Perf baseline

```bash
./scripts/run_perf_baseline.sh [text|csv|json]
```


## License

MIT. See `LICENSE`.


## Callback contract

Updater callbacks used via the C ABI must not unwind/panic across the FFI boundary. Return an error status instead.
