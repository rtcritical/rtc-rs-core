# ABI Risk Register (v0)

## Purpose
Track top ABI and semantic risks with mitigations and ownership.

| ID | Risk | Impact | Likelihood | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R1 | Pointer/length mismatch at ABI boundary | High | Medium | Strict arg validation, fuzz boundary APIs, parity tests | Core | Open |
| R2 | Ownership confusion (double-free/use-after-free) | High | Medium | Opaque handles, explicit ownership docs, sanitizer runs | Core | Open |
| R3 | Wrapper semantic drift from strict ABI | High | Medium | Canonical parity vectors + CI gate + mapping template | Wrappers | Open |
| R4 | Panic/abort crossing FFI boundary | High | Low-Med | Enforce non-throwing boundary, convert failures to status | Core | Open |
| R5 | Integer conversion/overflow bugs | Medium-High | Medium | Fixed-width boundary types, overflow checks, tests | Core | Open |
| R6 | Concurrency misuse across thread-confined contexts | Medium | Medium | Explicit threading contract docs + wrapper safeguards | Core/Wrappers | Open |
| R7 | JSON companion mismatch with nucleus semantics | Medium | Medium | Companion contract + vector-based conformance | Companion | Open |
| R8 | ABI breakage from nucleus changes | High | Low-Med | Governance policy + freeze + RFC exception path | Governance | Open |

## Review Cadence
- Revisit at each ADR milestone and before any MINOR release.
