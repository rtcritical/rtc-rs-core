# rtc-rs-core

RTCritical’s universal hierarchical data model library.

- Created in Rust
- Strict C ABI shim for cross-language / cross-platform use
- Companion JSON package strategy
- Clojure-inspired for simplicity and usability

## Status

**v0 complete** (feature-frozen; closeout checklist in `docs/v0-closeout.md`)

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
- v0 closeout matrix in `docs/v0-closeout.md`
- PM workflow under `.pm/`

## Tests

```bash
cargo test --tests
```

## Consumer C smoke harnesses

```bash
cargo build --release

# Static-link smoke
gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke.c target/release/librtc_rs_core.a -lpthread -ldl -lm -o /tmp/consumer_smoke
/tmp/consumer_smoke

# Shared-lib + callback smoke
gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke_callback.c -Ltarget/release -lrtc_rs_core -lpthread -ldl -lm -o /tmp/consumer_smoke_callback
LD_LIBRARY_PATH=target/release /tmp/consumer_smoke_callback
```

## Perf baseline

```bash
./scripts/run_perf_baseline.sh [text|csv|json]
```

## Release notes prep

```bash
# optional: set GITHUB_TOKEN for label-based categorization
./scripts/prepare_release_notes.py
cat dist/release_notes.md
```

Guardrail behavior:
- If merge commits exist in the release range, the script fails if categorization would emit zero assigned entries.
- This prevents silently publishing an empty-categories release note due to parsing/regression errors.
- When GitHub API metadata is available, bullets use PR titles (`<title> (#<n>)`) instead of raw merge commit subjects.

## License

MIT. See `LICENSE`.


## ABI safety contract (C FFI)

- `rtc_val*` values are **context-owned**. For mutating calls (`rtc_nassoc*`, `rtc_nupdate*`), all input/output values must belong to the provided `rtc_ctx*`.
- Null out-params are rejected; on error paths, out-pointers are cleared before return.
- Updater callbacks used via the C ABI must not unwind/panic across the FFI boundary. Return an error status instead.
- In debug builds (`debug_assertions`), additional pointer-liveness checks run to catch use-after-free / stale-pointer misuse early.
