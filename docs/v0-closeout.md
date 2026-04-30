# v0 Closeout

Status date: 2026-04-30

## Scope freeze

v0 is feature-frozen. New work after this point should be bugfixes, safety hardening, CI/release reliability, or docs clarifications only.

## v0 acceptance matrix

### Rust core behavior
- `cargo test --tests` passes.
- Core read/update semantics covered by `tests/core_*.rs` and `tests/api.rs`.

### C ABI contract
- Header: `include/core_v0.h`.
- ABI parity check passes: `./scripts/check_abi_parity.py`.
- ABI lifecycle/error-path coverage passes: `tests/abi_surface.rs`.

### Consumer validation
- Static-link smoke harness passes: `harness/consumer_smoke.c`.
- Shared-lib callback smoke harness passes: `harness/consumer_smoke_callback.c`.

### CI policy and governance
- CI jobs (`tests`, `consumer-smoke`, `policy`) are required and passing.
- PR-first branch protection enforced on `main`.
- Tag ruleset protection active for `refs/tags/v*`.

### Release pipeline
- Tag-triggered release workflow passes.
- Release uploads source tarball, headers tarball, and SHA256 checksums.
- Release notes generation is validated in production with:
  - category mapping,
  - non-empty assignment guard,
  - PR-title bullet formatting.

## Recommended closeout operator commands

```bash
# repo health
cargo test --tests
./scripts/check_changelog.sh
./scripts/check_abi_parity.py

# static consumer smoke
cargo build --release
gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke.c target/release/librtc_rs_core.a -lpthread -ldl -lm -o /tmp/consumer_smoke
/tmp/consumer_smoke

# shared callback smoke
gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke_callback.c -Ltarget/release -lrtc_rs_core -lpthread -ldl -lm -o /tmp/consumer_smoke_callback
LD_LIBRARY_PATH=target/release /tmp/consumer_smoke_callback
```

## Exit criteria

v0 is considered closed when the acceptance matrix above remains green on `main` and at least one post-closeout `v*` release confirms release workflow + artifact + notes behavior.
