# JSON Companion Contract (v0)

## Purpose
Define the strict boundary between the core collections nucleus and the JSON companion package.

## Scope
- Core nucleus: transport-agnostic hierarchical value model + operations
- JSON companion: JSON text/binary serialization behavior and interoperability policy

## Core vs Companion Responsibility Split

### Core nucleus (MUST)
- Own JSON-compatible value semantics (`nil/bool/number/string/array/object`).
- Own mutation/query semantics (`get/get_in/assoc/nassoc_in/update/nupdate_in`).
- Own strict status/error contracts and thread-confined context behavior.
- Remain serialization-agnostic.

### JSON companion (MUST)
- Provide encode/decode between core values and JSON documents.
- Preserve nucleus semantics where representable in JSON.
- Surface deterministic mapping for non-representable/extension types.
- Provide stable API contract for caller-controlled serialization behavior.

## Required Behavioral Mappings

1. Missing-path semantics
- Decoding/encoding layers MUST NOT alter core nil/missing semantics.

2. Numeric policy
- Core numeric nucleus is `i64` + `f64`.
- Large/high-precision numeric text beyond nucleus policy MUST follow documented conversion policy (error, string policy, or explicit option).

3. Object ordering
- JSON object ordering is non-semantic in nucleus and companion by default.
- Companion MUST NOT promise deterministic object key order unless explicit option is enabled.

4. YAML posture
- JSON-compatible YAML usage is allowed only under JSON-first subset constraints.
- YAML-specific features beyond JSON compatibility are out-of-scope for v0 companion guarantees.

## Extension Type Policy (v1+ hooks)

### Set mapping
- Set is not part of v0 nucleus JSON model.
- When v1 set extension is enabled, companion SHOULD support set->JSON-array encoding.
- Array->set decode requires explicit opt-in (schema/type hint/options).
- Set ordering in JSON output is non-deterministic by default.

## API Boundary Principles

- Canonical C ABI remains strict/status-based.
- Companion APIs may be ergonomic in host language wrappers but MUST preserve strict semantic parity.
- Companion MUST not bypass ownership/error/threading constraints defined by nucleus contract.

## Minimal v0 Companion API Surface (Draft)

- `json_encode_ex(ctx, value, opts, out_bytes)`
- `json_decode_ex(ctx, bytes, opts, out_value)`
- `json_validate_ex(ctx, bytes, opts, out_result)` (optional v0.1)

`opts` is extension-ready and may remain minimal/empty in initial v0.

## Conformance Expectations

- Companion behavior MUST be covered by wrapper parity tests + canonical vectors.
- Any companion-specific options MUST include deterministic defaults and documented status/error mappings.

## Deferred Items (allowed)

- Binary IPC extension integration details
- Rich schema-driven transforms
- Advanced canonicalization/ordering options
