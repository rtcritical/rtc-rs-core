# Set Extension (v1+) — Draft

## Intent
Add a high-utility set collection extension in v1+ while preserving JSON-core nucleus boundaries.

## Positioning
- Set is **not** part of v0 JSON-compatible nucleus.
- Set is an **ABI extension type** for non-JSON collection workflows.

## API Direction (Clojure-aligned)
- Core ops: `set_conj`, `set_disj`, `set_contains`
- Algebra ops: `set_union`, `set_intersection`, `set_difference`

## Boundary Rules
- JSON companion layer does not serialize sets by default.
- Any JSON crossing with sets requires explicit adapter/transform policy.

## Compatibility Goal
Maintain wrapper parity strategy used by nucleus:
- strict ABI semantics first
- ergonomic wrappers map to host-language idioms


## JSON Companion Interop Policy (v1+)
- Encode set values as JSON arrays for interoperability.
- Array element ordering is non-deterministic by default.
- Decoding array -> set requires explicit opt-in (schema hint or options) to avoid ambiguous coercion.

## Options-Map Extension Pattern (v1+)
- Future extension APIs may expose `*_with_opts` signatures for behavior tuning.
- Options values should use the same map/value model for consistency.
- Candidate early option: `get/get_in` default value override while preserving nucleus baseline semantics.


Related extension: `docs/spec/user-object-extension-v1.md` (custom opaque objects, non-nucleus).
