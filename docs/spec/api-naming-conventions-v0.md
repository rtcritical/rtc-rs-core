# API Naming Conventions (Locked)

Rust `api` module naming:
- Scalars: `nil`, `b`, `i`, `f`, `st`
- Constructors:
  - map empty: `m()`
  - vector primary macro: `v!()` / `v!(...)`
  - set primary macro: `s!()` / `s!(...)`
  - from collection: `m_from`, `v_from`, `s_from`
- Keys: `k` for string-key, `idx` for index-key

Path/ops surface:
- `get_in`, `assoc_in`, `update_in` are string-path-first in `api`.
- Index-heavy access should prefer vector helpers (`v_get`, `v_assoc`, `v_update`) so index key internals remain mostly opaque.
