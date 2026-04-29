# API Naming Conventions (Locked)

Rust `api` module naming:
- Scalars: `nil`, `b`, `i`, `f`, `st`
- Map/vector/set constructors:
  - empty: `m_empty`, `v_empty`, `s_empty`
  - from collection: `m_from`, `v_from`, `s_from`
- Keys: `k` for string-key, `idx` for index-key

Path/ops surface:
- `get_in`, `assoc_in`, `update_in` are string-path-first in `api`.
- Index-heavy access should prefer vector helpers (`v_get`, `v_assoc`, `v_update`) so index key internals remain mostly opaque.
