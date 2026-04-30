# ABI compatibility policy (v0)

## Scope

Applies to the strict C ABI defined in `include/core_v0.h` for v0.x releases.

## Compatibility rules

### Disallowed in v0.x (breaking)

- Removing an exported `rtc_*` function from the published ABI surface.
- Renaming an exported `rtc_*` function.
- Changing an exported function signature in a way that breaks existing compiled consumers.

### Allowed in v0.x (non-breaking by default)

- Adding new exported `rtc_*` functions.
- Internal Rust implementation changes that preserve existing ABI behavior.
- Documentation clarifications with no ABI signature changes.

## Enforcement

CI policy uses:
- `scripts/check_abi_parity.py` to ensure header/export parity.
- `scripts/check_abi_compat_policy.py` to ensure no removals against v0 symbol baseline.

Baseline file:
- `docs/spec/abi-v0-symbol-baseline.txt`

## Intentional breaking changes

Breaking ABI changes require explicit major-version planning and baseline/version policy updates as part of the version bump.
