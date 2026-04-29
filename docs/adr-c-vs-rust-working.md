# ADR (Working): C vs Rust for Cross-Language Libraries

- **ADR ID:** ADR-014 (working draft)
- **Date:** 2026-04-29
- **Status:** Working / Candidate
- **Owner:** Clio + Nick
- **Scope:** Core library implementation language and cross-language strategy for x-language support (Python, Java, etc.)

---

## Context

We want high-performance, low-overhead libraries that are compatible across languages/frameworks via a stable interface, while remaining safe and intuitive for downstream users.

This library is intended to become a foundational building block across most RTCritical projects, so design quality at the ABI and data-model levels is strategic.

Most target ecosystems (Python, Java/JNI, Node, Go, etc.) interoperate most broadly via **C ABI**.

Questions raised:

1. Is a C library automatically cross-language compatible?
2. If Rust compiles to a C ABI surface, does that preserve safety and intuition?
3. Does Rust->C ABI add extra breakage/security risk vs implementing directly in C?
4. How should shared-memory interaction work for JSON-like structures?

---

## Key Findings

### 1) “Written in C” is not enough by itself

A library is broadly interoperable when it exports a **well-designed, stable C ABI contract**:

- C-callable function symbols
- C-compatible data layouts at boundary
- Explicit ownership/lifetime semantics
- Versioning policy
- Clear error contract

So, not “automatic,” but very achievable with ABI discipline.

### 2) Rust can be an excellent implementation language for a C ABI library

Rust can expose a C ABI boundary while keeping most internals memory-safe and easier to reason about.

- **Kept:** cross-language compatibility, performance, low overhead
- **Not carried across boundary automatically:** Rust lifetimes/borrow guarantees

Therefore: Rust improves implementation safety, but the ABI boundary still requires C-style contracts.

### 3) FFI boundary is the risk hotspot (for both C and Rust)

Typical failure/security risks at ABI boundary:

- invalid pointers
- length/pointer mismatches
- use-after-free / double-free across ownership confusion
- thread-safety misuse
- unchecked panics crossing boundary (Rust-specific concern if unhandled)

Rust does not remove boundary risk, but often reduces total risk by concentrating unsafe operations into a smaller, auditable shim layer.

### 4) Shared memory and heap graphs

In both C and Rust:

- Normal in-process heap graphs are process-local.
- Raw pointer-based structures are not directly portable across processes.
- Same executable does not guarantee pointer validity across processes.

For cross-process data exchange:

- Share serialized bytes (JSON or binary format), then deserialize per process, **or**
- Design shared-memory-native layouts using offsets/handles (not raw pointers).

---

## Essence Statement (Working)

This initiative defines a **universal hierarchical data-model library** exposed through a stable **C ABI**, with these core properties:

- **JSON-compatible core model** for broad interoperability
- **IPC-capable architecture direction** (including extension tracks for efficient binary interchange)
- **Clojure-inspired collections semantics and utility operations** for simplicity, robustness, and predictable behavior

In short: a foundational, cross-platform collections/data-model substrate for RTCritical systems that prioritizes safe contracts, durable API design, and long-term extensibility.

---

## High-Level Product Goals (Working)

1. Provide a **safe, intuitive, error-resistant, highly compatible C ABI** for high-performance, highly concurrent systems.
2. Provide **JSON-compatible nested data structures** with strong performance on deep/large nested operations.
3. Keep the core library **simple, powerful, robust, flexible, and lightweight** so it can be reused broadly across RTCritical.
4. Keep function/data-structure APIs coherent: data model + operations should be designed together, not as separate concerns.
5. Treat this library as a **foundational cross-platform collections layer** (Clojure-collections-inspired for JSON-compatible types) used broadly across RTCritical systems.

---

## Rust API + C ABI Layering Question (Working Direction)

If implemented in Rust, we should likely ship **both**:

- a native Rust API for Rust-to-Rust usage (lowest overhead, strongest ergonomics/safety)
- a stable C ABI API for cross-language integration

Rationale:

- Rust callers should not be forced through C FFI when not needed.
- C ABI remains the compatibility contract and primary interop test surface.
- We can test both layers explicitly: Rust-native behavior + ABI stability/robustness.

---

## Locked Decisions (Current)

1. **Core nucleus is frozen**
   - Includes: value model/types, ownership+error model, core nested ops, path/key semantics, and thread-safety contract.
   - Additive helper/extension APIs are allowed outside the nucleus.

2. **JSON companion strategy**
   - Keep companion JSON API in the same repo as a separate package.
   - Co-develop with core during initial phase to keep constraints aligned.
   - It is acceptable for a large share of behavioral testing to flow through JSON API entrypoints.

3. **Binary IPC/shared-memory exploration track**
   - Treat as a formal exploration stream, not a casual nice-to-have.
   - Required outputs: format/spec draft, reference prototype, and benchmark comparison against JSON text encode/decode.
   - Adoption decision is evidence-gated.

4. **Boundary placement**
   - Binary IPC/shared-memory format is an adjacent extension track, not part of frozen core nucleus.

5. **Public C ABI surface style**
   - Public C ABI SHALL expose strict, explicit status/result contracts as the canonical interface.
   - Ergonomic behavior layers SHALL be provided as language-appropriate wrappers (and optional C convenience layer), not as the canonical ABI contract.
   - Conformance tests SHALL validate semantic parity between strict ABI and ergonomic wrappers.

6. **Clojure-compatible missing-target update semantics**
   - `update`/`update_in` missing-target behavior SHALL apply updater to `nil` (Clojure-compatible) rather than hard failure by default.

7. **Error message API policy (v0 nucleus)**
   - v0 nucleus SHALL expose `rtc_last_error_message(ctx)` as the human-readable error companion to strict status codes.
   - Explicit buffer-copy error message APIs are deferred and SHALL remain out of nucleus unless a concrete integration need is proven.

---

## Core Nucleus Specification (Draft, Normative)

The following nucleus contract is normative and MUST remain stable once ratified.

1. **Value model (JSON-compatible core)**
   - Core value kinds MUST be limited to: `nil`, `bool`, `number`, `string`, `array`, `object`.
   - Numeric representation in nucleus MUST be `i64` and `f64`.
   - Very large or high-precision numeric payloads SHOULD be represented as strings by policy at integration boundaries.

1a. **ABI boundary integer-width policy**
   - ABI boundary integer widths SHALL be fixed-width for cross-platform stability.
   - `int64_t` SHALL be used for signed numeric values and index keys.
   - `uint64_t` SHALL be used for lengths/counts/capacities at the ABI boundary.

2. **Core operation surface**
   - Nucleus operation family MUST include: `get`, `get_in`, `assoc`, `assoc_in`, `update`, `update_in` (plus direct path/index variants as needed by ABI ergonomics).
   - Semantics MUST be Clojure-inspired and nil-tolerant where practical.
   - Nested assoc/update flows MUST default toward predictable path-creation behavior instead of brittle caller burden.

3. **Ownership and memory contract**
   - Values MUST be owned by explicit library context/handle boundaries.
   - Ownership transfer and borrowing rules MUST be explicit in ABI docs.
   - Hidden cross-context aliasing MUST be disallowed.

4. **Error contract**
   - ABI-visible behavior MUST be deterministic and non-throwing.
   - Errors MUST be represented via stable status/result contracts (with optional message retrieval).
   - No panic/abort behavior SHALL cross ABI boundaries.

5. **Threading contract (nucleus)**
   - Nucleus operations MUST be single-threaded by design.
   - Contexts MUST be thread-confined unless explicitly transferred by caller-managed synchronization/ownership handoff.
   - Internal parallelism SHALL be out-of-scope for nucleus.

6. **Object/map ordering semantics**
   - Object/map ordering MUST be unspecified in nucleus semantics.
   - Optional insertion-order-preserving behavior, if ever added, SHALL be extension-level and non-core.

7. **JSON-companion relationship**
   - JSON encode/decode SHALL NOT be required inside core nucleus implementation.
   - A companion JSON package MUST be co-designed in the same repo with aligned constraints and contracts.
   - Core MUST remain transport-agnostic; companion JSON layer SHALL provide serialization boundary behavior.

8. **YAML compatibility posture**
   - JSON-compatible YAML usage SHALL be supported only under JSON-compatibility-first constraints.
   - YAML-specific semantics beyond the JSON-compatible subset SHALL be out-of-scope for nucleus.

---

## Decision Direction (Current)

### Candidate Decision A

Adopt **C ABI as the canonical interop boundary** for cross-language compatibility.

### Candidate Decision B

Prefer **Rust for implementation** when feasible, with a small, strict `extern "C"` shim and stable C headers.

### Candidate Decision C

Treat ABI boundary design as a first-class engineering surface (not an afterthought), with explicit ownership, error, and threading contracts.

---

## Recommended ABI Design Rules (v0)

1. **Opaque handles over exposed structs** where possible.
2. **Create/free pairs** for owned resources.
3. **Pointer + length pairs** for buffers; never length-less pointers.
4. **No Rust-specific types in public ABI.**
5. **No panics across FFI boundary** (convert to error status).
6. **Deterministic error model** (status codes + optional error message retrieval API).
7. **Version negotiation / symbol versioning** strategy from day one.
8. **Documented threading model** per handle/function.
9. **Stable memory ownership table** in docs (caller-owned vs callee-owned).
10. **Fuzz + sanitizer coverage** focused on boundary functions.

---

## Tradeoff Summary

### C implementation + C ABI

- **Pros:** simplest conceptual mapping to ABI, no language bridge layer
- **Cons:** larger unsafe surface in implementation, more manual memory correctness burden

### Rust implementation + C ABI

- **Pros:** stronger internal safety, clearer invariants, often lower defect/security risk overall
- **Cons:** must carefully constrain boundary and avoid leaking Rust semantics/types through ABI

Net: Rust + disciplined C ABI is often the best balance for our goals.

---

## Proposed Delivery Scope (v0 vs v1+)

### v0 (must-have)

- Stable C ABI surface for core nested data operations (create/read/update/delete + traversal helpers).
- Explicit ownership/error/threading contract documentation for all ABI functions.
- JSON-compatible value model as the core scope (independent of transport/serialization concerns).
- Rust-native API (if Rust implementation is selected) for same-language low-overhead usage.
- Cross-language smoke coverage for initial wrapper targets (at minimum Python + Java/JNI).
- Boundary-focused validation gates (fuzz + sanitizer + ABI compatibility checks).
- A clear companion-library contract for JSON encode/decode so serialization integrates cleanly without bloating core scope.

### v1+ (planned expansion)

- Expanded wrapper ecosystem (Node, Go, and additional language bindings).
- Optional advanced query/path ergonomics and bulk-update APIs.
- Optional internal persistent/immutable collection acceleration paths (without changing C ABI contract).
- Additional schema-driven helpers and richer typed-codegen integration.
- Performance specialization tracks for very large nested payload workloads.
- Companion JSON encode/decode library hardening and optimization (kept as separate minimal layer).

### v1+ Set Extension Track (non-JSON core extension)

- Add `set` as an extension collection type exposed through the C ABI.
- Keep `set` explicitly out of the JSON core value model and out of default JSON companion semantics.
- Provide Clojure-aligned set operations in extension namespace: `conj`, `disj`, `contains`, `union`, `intersection`, `difference`.
- Require explicit conversion/adapter policy when crossing JSON boundaries.

### v1+ JSON Companion Set Mapping Policy

- JSON companion SHOULD support encoding `set` values as JSON arrays for interop.
- Set ordering in JSON output is non-deterministic unless an explicit ordering strategy is requested.
- Decoding JSON arrays back into `set` SHOULD require explicit opt-in (schema/type hint/options) to avoid accidental type assumptions.

### v1+ Options-Map Overload Pattern

- Consider optional `*_with_opts` API variants across core operation families in v1+ extensions.
- Options payload SHOULD use the same map/value model exposed by the library to preserve internal consistency.
- Initial candidate option: default-value behavior for `get/get_in` variants, while keeping nucleus defaults unchanged.

### Scope posture

- Keep v0 intentionally small, stable, and hard to misuse.
- Expand power/features in v1+ without destabilizing ABI commitments.

---

## Strict ABI Function Behavior Matrix (Draft)

Status basis uses the locked v0 nucleus status set:
`RTC_OK`, `RTC_ERR_INVALID_ARG`, `RTC_ERR_TYPE`, `RTC_ERR_BOUNDS`, `RTC_ERR_OOM`, `RTC_ERR_OVERFLOW`, `RTC_ERR_STATE`, `RTC_ERR_INTERNAL`.

### `get_ex(root, key, out)`
- Missing key/path element: returns `out=nil` with `RTC_OK`.
- Wrong container type for requested key/index operation: `RTC_ERR_TYPE`.
- Invalid arguments (null output pointer, malformed key descriptor, etc.): `RTC_ERR_INVALID_ARG`.

### `get_in_ex(root, path, out)`
- Missing segment at any step: returns `out=nil` with `RTC_OK`.
- Wrong intermediate type during traversal: `RTC_ERR_TYPE`.
- Invalid arguments/path descriptor: `RTC_ERR_INVALID_ARG`.

### `assoc_ex(ctx, root, key, val, out)`
- Success returns updated value with `RTC_OK`.
- Wrong root container type for key operation: `RTC_ERR_TYPE`.
- Invalid arguments: `RTC_ERR_INVALID_ARG`.

### `assoc_in_ex(ctx, root, path, val, out)`
- Missing path segments are created by default and return `RTC_OK`.
- Type conflict that prevents path creation/traversal: `RTC_ERR_TYPE`.
- Invalid arguments/path descriptor: `RTC_ERR_INVALID_ARG`.

### `update_ex(ctx, root, key, fn, user_data, out)`
- Missing key applies updater to `nil` (Clojure-compatible), returns `RTC_OK` on success.
- Wrong container type for key operation: `RTC_ERR_TYPE`.
- Invalid function/context/arguments: `RTC_ERR_INVALID_ARG` or `RTC_ERR_STATE` as applicable.

### `update_in_ex(ctx, root, path, fn, user_data, out)`
- Missing target applies updater to `nil` (Clojure-compatible), returns `RTC_OK` on success.
- Type conflict during traversal/path creation: `RTC_ERR_TYPE`.
- Invalid arguments/path/function: `RTC_ERR_INVALID_ARG`.

### Cross-cutting outcomes (all strict ABI functions)
- Allocation failure: `RTC_ERR_OOM`.
- Numeric overflow/conversion overflow: `RTC_ERR_OVERFLOW`.
- Invalid/closed/corrupt context or handle: `RTC_ERR_STATE`.
- Unexpected invariant failure: `RTC_ERR_INTERNAL`.

### Deliberate omission
- `NOT_FOUND` is intentionally omitted from nucleus strict semantics for read traversal; missing keys/paths are modeled as `nil + RTC_OK`.

---

## Decision Matrix Recommendation (Current)

Given the accepted weighting priorities (including Strategic Ecosystem Leverage), the current recommended implementation direction is:

- **Rust-core + strict C ABI shim** as canonical path

Rationale summary:
- Preserves C ABI portability for cross-language use
- Improves internal safety/evolvability for foundational long-lived systems code
- Better aligns with direct internal reuse across upcoming RTCritical projects without forcing all internal use through FFI

This recommendation remains subject to change only if feasibility evidence (delivery risk, toolchain constraints, benchmark regressions) materially contradicts current assumptions.

---

## Implementation Path Decision (v0)

### Chosen Path
- **Rust-core + strict C ABI shim** is the selected v0 implementation path.

### Why
- Best alignment with weighted decision matrix, including Strategic Ecosystem Leverage.
- Preserves C ABI portability for multi-language interoperability.
- Improves internal safety/evolvability for long-lived systems foundations.

### Fallback/Revisit Triggers
Revisit this decision only if one or more are observed with evidence:
1. Material delivery-risk regression vs plan
2. Unacceptable toolchain/deployment constraints
3. Benchmark or conformance regressions that cannot be mitigated within agreed scope/timeline

---

## Open Questions

1. Which error contract variant do we standardize on first?
   - return status + out params
   - result struct return
2. Should we include a standard allocator hook strategy in v0?
3. Which compatibility targets are first-class in v0 wrappers?
   - Python, Java/JNI, Node, Go (priority order)
4. Do we define ABI stability by semantic version major only, or stricter symbol policy?
5. What is the minimal, strict interface between core collections library and companion JSON encode/decode library?
6. Should companion JSON support begin as one reference implementation or multiple interchangeable adapters?
7. What is the measured call-boundary overhead of C ABI usage for our target operation mix?
8. Should we define a binary interchange/shared-memory format so multi-process communication can avoid JSON text encode/decode when both sides share the ABI contract?

---

## Initial Validation/Quality Gates (Proposal)

- ABI header lint/check (public headers only use C-compatible types)
- Cross-compiler build matrix
- Boundary fuzz targets
- ASAN/UBSAN (and TSAN where relevant)
- Simple wrapper smoke tests in at least Python + Java/JNI
- Microbench suite isolating C ABI call overhead vs in-process/native calls for representative nested operations
- Binary interchange prototype benchmarks vs JSON text encode/decode for multi-process IPC paths

---

## Working Notes

This ADR is intentionally a **working document** and will be extended with additional findings.

---

## Appendix A: Decision Matrix (Working)

Scoring: 1 (weak) to 5 (strong). Weights are provisional and can be tuned.

| Dimension | Weight | C impl + C ABI | Rust impl + C ABI | Notes |
|---|---:|---:|---:|---|
| Runtime performance ceiling | 5 | 5 | 5 | Both can be excellent when well engineered |
| Startup/footprint | 4 | 5 | 4 | Rust usually close; may add minor binary/runtime overhead |
| Implementation memory safety | 5 | 2 | 5 | Rust advantage inside core |
| FFI boundary safety | 5 | 3 | 3 | Boundary discipline required in both |
| Cross-language reach | 5 | 5 | 5 | Same if C ABI contract is solid |
| API intuitiveness for wrappers | 4 | 4 | 4 | Mostly ABI design dependent |
| Native API ergonomics/perf (same-language) | 4 | 3 | 5 | Rust-native API can avoid FFI overhead for Rust callers |
| JSON schema ecosystem fit | 4 | 3 | 5 | Rust has strong `jsonschema` + `schemars` path |
| JSON nested DS + encode/decode ecosystem | 5 | 3 | 5 | Rust has strong off-the-shelf options; C may require more custom work |
| Persistent/immutable collection support (internal option) | 2 | 2 | 4 | More mature ergonomic options on Rust side; ABI still C-shaped |
| Tooling/debug familiarity | 3 | 5 | 3 | Team-dependent; C often more familiar in low-level stacks |
| Long-term defect/security risk | 5 | 2 | 4 | Rust tends to reduce memory-corruption class defects |
| Hiring/onboarding friction | 3 | 4 | 3 | Depends on team mix |
| Total (weighted, provisional) | — | **167** | **216** | Indicates Rust-core advantage under safety-heavy goals |

### Matrix interpretation

- This matrix treats ABI as one major axis, not the only axis.
- If our priority stack is safety + low defect rate + performance, Rust-core with strict C ABI shim currently leads.
- If short-term delivery speed with existing C-heavy staff dominates, C may still be preferred for selected components.

### Matrix v2 (Reweighted for Platform Strategy)

To reflect RTCritical platform direction, add:
- **Strategic Ecosystem Leverage (Internal Platform Fit)**: how well the language becomes a default internal systems foundation while still serving cross-language ABI goals.

Reweighted criteria (total 100):
- API safety + misuse resistance: 20
- ABI stability/compatibility: 18
- Semantic clarity/consistency: 12
- Evolvability behind frozen nucleus: 12
- Time-to-v0 delivery: 13
- Performance headroom (future): 8
- Strategic Ecosystem Leverage (Internal Platform Fit): 17

Directional outcome (v2): Rust-core + strict C ABI remains preferred, with stronger advantage under internal platform leverage weighting.



## Consequences

### Positive
- Stronger safety posture for foundational systems code while preserving broad ABI portability.
- Clear nucleus freeze + governance path reduces long-term ecosystem drift.
- Wrapper parity approach supports ergonomic APIs without sacrificing canonical behavior.

### Costs/Tradeoffs
- Requires disciplined FFI boundary design/testing.
- Adds governance and parity-testing overhead up front.
- Requires maintaining both strict ABI contract and wrapper mappings.

---


## Deferred Items

- **Item:** Binary IPC extension adoption decision
- **Reason deferred:** Requires spec + reference prototype + benchmark evidence
- **Owner:** Nick + Clio
- **Target date:** 2026-05-31
- **Risk if delayed:** IPC optimization opportunities remain unquantified
- **Fallback plan:** Continue with JSON companion path while keeping binary IPC track active

- **Item:** Set extension implementation (`set` ABI type + ops)
- **Reason deferred:** v1+ scope to preserve v0 nucleus focus
- **Owner:** Nick + Clio
- **Target date:** 2026-06-30
- **Risk if delayed:** Delayed non-JSON collection utility expansion
- **Fallback plan:** Keep transformation patterns in wrappers until extension is implemented

---


## Related Specs and Artifacts

- `docs/spec/v0-nucleus.h`
- `docs/spec/wrapper-parity-tests.md`
- `docs/spec/parity-vectors-v0.md`
- `docs/spec/wrapper-status-mapping-template-v0.md`
- `docs/spec/json-companion-contract-v0.md`
- `docs/spec/governance-and-versioning-v0.md`
- `docs/spec/abi-risk-register-v0.md`
- `docs/spec/toolchain-reproducibility-v0.md`
- `docs/spec/adr-closure-checklist-v0.md`
- `docs/spec/set-extension-v1.md`

