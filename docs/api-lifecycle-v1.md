# API Lifecycle and Versioning Notes (v1)

## Scope stance

- `core_v0.h` remains the stable ABI contract line.
- Breaking ABI changes require a new major surface/versioned header path.

## Change classes

1. **Patch-safe**
   - bug fixes, docs clarifications, additional tests, non-breaking internal changes.
2. **Minor additive**
   - additive behavior that does not alter existing ABI contracts.
   - must include compatibility notes and tests.
3. **Breaking**
   - symbol removal/rename, signature/type changes, semantic incompatibilities.
   - requires explicit approval, migration notes, and versioned contract transition.

## Deprecation guidance

- Prefer additive replacement first.
- Mark deprecated behavior in docs/spec with rationale and sunset criteria.
- Maintain deprecation window long enough for downstream consumers to migrate.

## Governance hooks

- Align with `docs/abi-compat-policy.md` and CI ABI checks.
- Record lifecycle-impacting decisions in PM evidence/decisions.
