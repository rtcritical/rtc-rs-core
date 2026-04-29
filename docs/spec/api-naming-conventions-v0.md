# API Naming Conventions (Locked)

Rust `api` module naming:
- Scalars: `nil`, `b`, `i`, `f`, `st`
- Constructors:
  - map primary macro: `m!()` / `m!(("k", v), ...)`
  - vector primary macro: `v!()` / `v!(...)`
  - set primary macro: `s!()` / `s!(...)`
  - from collection: `m_from`, `v_from`, `s_from`
- Keys: `k` for string-key, `idx` for index-key

Path/ops surface:
- `get_in`, `assoc_in`, `update_in` are string-path-first in `api`.
- Index-heavy access should prefer vector helpers (`v_get`, `v_assoc`, `v_update`) so index key internals remain mostly opaque.


Role split (intentional):
- `m!` is the literal constructor at call sites (`m!()`, `m!(("k", v), ...)`).
- `m_from` is the runtime ingest constructor from iterable tuple outputs
  (e.g., map/reduce/filter pipelines, decoded/transformed records).


Mutable naming (Common Lisp-style n*):
- API primary mutable ops: `nassoc`, `nassoc_in`, `nupdate`, `nupdate_in`
- ABI primary mutable ops: `rtc_nassoc_ex`, `rtc_nassoc_in_ex`, `rtc_nupdate_ex`, `rtc_nupdate_in_ex`
- Legacy names (`assoc_in/update_in`, `rtc_assoc_ex/...`) remain as compatibility aliases and are reserved for future immutable semantics.
