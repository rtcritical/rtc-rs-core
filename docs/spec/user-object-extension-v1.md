# User Object Extension (v1, Non-Nucleus)

## Purpose
Allow consumers to store and pass custom application objects through collection operations without modifying the frozen JSON-compatible core.

## Scope
- Extension-only value kind for user objects.
- Nucleus remains unchanged (`nil/bool/number/string/array/object`).
- JSON companion remains unchanged for v0 core behavior.

## Design Goals
1. No core contract breakage.
2. Preserve Clojure-ish nil-safe traversal semantics.
3. Support internal + external consumers needing non-JSON values.
4. Keep ABI safety explicit around ownership and callbacks.

## Extension Value Model
Introduce extension value kind:
- `RTC_EXT_USER_OBJECT`

Payload shape (conceptual):
- opaque pointer/handle
- type id (u64 or namespaced string id)
- optional hash callback
- optional equality callback
- optional destructor callback
- optional clone/retain callback (if shared ownership is needed)

## Semantic Rules

### Traversal safety
- `get/get_in` and variants treat user object as **non-traversable**.
- If traversal continues through user object, result is `nil + RTC_OK` (Clojure-ish behavior).

### Assoc/update
- User object values are assignable like any other value.
- `update/update_in` missing-target behavior remains unchanged (updater gets nil-equivalent).

### Map keys policy (phased)
- v1 initial: user objects allowed as **values only**.
- Optional later phase: keys allowed only when hash+eq+stability constraints are explicitly satisfied.

## ABI Safety Contract
- Library never dereferences user object payload directly.
- Callback invocation rules are strict and synchronous.
- No callback/user_data retention beyond call unless explicit retain/release contract exists.
- No callback re-entrancy guarantees on same context unless explicitly documented.

## Ownership/Lifetime Contract (v1 default)
- Caller owns object memory unless explicit ownership transfer API is used.
- If destructor callback is registered for a value instance, library may invoke it at value/context release according to declared ownership mode.

## JSON Boundary Behavior
- JSON companion does not serialize user objects by default.
- Encoding behavior for user objects must be explicit policy (error, redaction, custom adapter), outside core.

## Compatibility Statement
This extension is additive and does not modify core types/semantics/status taxonomy.


## Future Extension Note: Generic Map Keys
A future extension may introduce generic map-key support (`(Value, Value)` pairs) without changing frozen core behavior.

Compatibility strategy:
- Keep core/public v0 API semantics string-key-first for JSON-compatible object behavior.
- Introduce generic-key map as an additive extension namespace/type in v1+.
- Preserve existing APIs; add opt-in extension APIs rather than mutating current signatures.

This provides a migration path to richer key types without breaking current API contracts.
