# ADR Closure Checklist (v0)

## Purpose
Define objective gates for moving the C vs Rust working ADR to final/accepted status.

## Exit Rule
ADR can be marked **Accepted** only when all required gates below are satisfied or explicitly deferred with owner/date/rationale.

---

## Live Status Snapshot (2026-04-29)

- **A Core Contract Freeze:** DONE
- **B JSON Companion Alignment:** DONE
- **C Wrapper Parity Readiness:** DONE
- **D Feasibility Evidence:** DONE
- **E Decision Matrix Completion:** PARTIAL (weights + evidence citations + recommendation pending)
- **F Binary IPC Extension Track:** OPEN (conditional/defer-capable)
- **G Governance + Versioning:** DONE
- **H Final ADR Packaging:** OPEN

---

## A. Core Contract Freeze (Required)

- [x] Core nucleus scope is frozen and documented (types, ops, semantics).
- [x] Strict C ABI style decision is frozen.
- [x] Status-code taxonomy is frozen.
- [x] Function behavior matrix is frozen.
- [x] Integer boundary policy is frozen (`int64_t` values/index, `uint64_t` lengths/counts).
- [x] Threading contract is frozen (thread-confined contexts).
- [x] Map ordering semantics are frozen (unspecified in nucleus).

Artifacts:
- `docs/adr-c-vs-rust-working.md`
- `docs/spec/v0-nucleus.h`

---

## B. JSON Companion Alignment (Required)

- [x] Companion JSON package boundary/contract documented.
- [x] JSON-compatible-YAML posture documented (JSON-first subset constraints).
- [x] Core vs companion responsibility split is explicit and non-overlapping.

Artifacts:
- ADR + companion package README/spec

---

## C. Wrapper Parity Readiness (Required)

- [x] Wrapper parity test spec approved.
- [x] Canonical parity vector pack approved.
- [x] Status mapping table template defined for wrappers.
- [x] CI gate policy defined (wrapper release blocked on parity failures).

Artifacts:
- `docs/spec/wrapper-parity-tests.md`
- `docs/spec/parity-vectors-v0.md`

---

## D. Feasibility Evidence (Required)

- [x] At least one strict ABI reference implementation path is identified (C-core or Rust-core+C ABI).
- [x] Risk register includes top ABI hazards and mitigations.
- [x] Build/toolchain reproducibility path documented for reference implementation.

Artifacts:
- implementation plan doc + risk log

---

## E. Decision Matrix Completion (Required)

- [x] Scoring dimensions finalized (hard gates + scored criteria).
- [ ] Weights finalized.
- [ ] Evidence references attached for each scored claim.
- [ ] Recommendation statement drafted with rationale.

Artifacts:
- ADR Appendix A + supporting benchmark/analysis notes

---

## F. Binary IPC Extension Track (Conditionally Required)

Required before marking extension “Adopted”; not required to finalize nucleus ADR if explicitly deferred.

- [ ] Binary format/spec draft exists.
- [ ] Reference prototype exists.
- [ ] Benchmarks compare binary IPC vs JSON text path.
- [ ] Adoption decision recorded (Adopt/Defer/Reject) with evidence.

Artifacts:
- extension spec + benchmark report

---

## G. Governance + Versioning (Required)

- [x] ABI versioning policy finalized.
- [x] Change-control process for frozen nucleus defined (RFC/exception path).
- [x] Backward-compat policy documented for wrappers.

Artifacts:
- ADR governance section + versioning policy doc

---

## H. Final ADR Packaging (Required)

- [ ] ADR status changed from Working/Candidate to Accepted.
- [ ] “Consequences” section completed (what we gain/lose).
- [ ] “Deferred Items” section completed with owners/dates.
- [ ] Cross-links to specs/tests added and validated.

Artifacts:
- final ADR commit

---

## Deferred Item Format (Mandatory)

Use this exact schema for any deferred gate:
- **Item:**
- **Reason deferred:**
- **Owner:**
- **Target date:**
- **Risk if delayed:**
- **Fallback plan:**
