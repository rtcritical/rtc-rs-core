# Consumer Quickstart (v1)

This guide shows the minimum compile/run path for C consumers using release build outputs.

## Prerequisites

- Rust toolchain (stable)
- C compiler (`gcc` assumed in examples)

## 1) Build release artifacts

```bash
cargo build --release
```

## 2) Static-link smoke path

```bash
gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke.c target/release/librtc_rs_core.a -lpthread -ldl -lm -o /tmp/consumer_smoke
/tmp/consumer_smoke
```

Expected output includes `consumer_smoke:ok`.

## 3) Shared-lib callback smoke path

```bash
gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke_callback.c -Ltarget/release -lrtc_rs_core -lpthread -ldl -lm -o /tmp/consumer_smoke_callback
LD_LIBRARY_PATH=target/release /tmp/consumer_smoke_callback
```

Expected output includes `consumer_smoke_callback:ok`.

## Notes

- Static path is a required release verification path.
- Shared path is best-effort in v1 but strongly recommended for callback integration confidence.
