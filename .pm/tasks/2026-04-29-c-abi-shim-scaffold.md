# Task: C ABI shim scaffold

- **Owner:** Nick + Clio
- **Status:** IN_PROGRESS
- **Goal:** Create strict C ABI shim boundary matching `docs/spec/v0-nucleus.h`.
- **Acceptance:**
  - exported symbol map draft
  - compileable shim stubs
  - status/error plumbing hooks


## Progress
- Added Rust `extern "C"` shim skeleton with strict status enum and context lifecycle fns.
- Added baseline constructor surface (`rtc_nil`, `rtc_bool`, `rtc_i64`, `rtc_f64`, `rtc_strn`) and value free helper.
- Copied frozen ABI draft header into `include/v0-nucleus.h` for alignment review.

- rtc_get_ex/rtc_get_in_ex wired to core ops.

- rtc_assoc_ex/rtc_assoc_in_ex wired to core ops.

- rtc_update_ex/rtc_update_in_ex wired to core ops.

- Added user-object extension direction as non-nucleus additive spec (v1).
