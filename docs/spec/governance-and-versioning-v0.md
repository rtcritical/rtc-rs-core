# Governance and Versioning Policy (v0)

## Purpose
Define how the frozen nucleus can evolve safely without breaking downstream ecosystems.

## Policy Summary

- The nucleus contract is frozen once ratified.
- Public C ABI is canonical and stability-critical.
- Change to frozen nucleus requires explicit governance process.

## Versioning Model

### SemVer baseline
- `MAJOR`: breaking changes
- `MINOR`: additive, backward-compatible
- `PATCH`: bugfixes/no contract breaks

### Nucleus freeze override
For frozen nucleus items, breaking changes are extraordinary and require exception governance (not routine major bump behavior).

## Change Classes

1. **Nucleus-breaking (high bar)**
- Changes to core value model, core op semantics, status taxonomy, ownership/threading contract, or ABI signatures.
- Requires formal exception RFC and explicit approval.

2. **Nucleus-additive (normal path)**
- Additive APIs/extensions outside frozen nucleus.
- Must not alter existing semantic contracts.

3. **Wrapper-only changes**
- Ergonomic improvements allowed if strict parity with canonical ABI is maintained.

## Governance Workflow (Required)

1. Author change proposal (RFC-lite)
   - problem statement
   - affected contract surface
   - compatibility impact
   - migration strategy
   - rollback plan

2. Classification
   - nucleus-breaking vs additive vs wrapper-only

3. Required evidence
   - parity tests
   - ABI compatibility checks
   - risk assessment

4. Decision record
   - approved/rejected/deferred
   - owner/date
   - rationale

## Exception Path (Frozen Nucleus)

A nucleus-breaking exception MUST include:
- demonstrated critical defect or unavoidable platform/security requirement
- compatibility mitigation plan
- migration tooling/docs strategy
- explicit downstream impact sign-off

## ABI Compatibility Rules

- Existing exported symbols/signatures MUST remain stable across MINOR/PATCH.
- Deprecations MUST include timeline and compatibility window.
- Symbol/version policy MUST be documented before GA.

## Wrapper Backward-Compat Policy

- Wrappers MUST preserve semantic parity with strict ABI.
- Wrapper major versions MAY track language-ecosystem needs, but parity guarantees are mandatory.
- Wrapper release CI MUST include canonical parity vectors.

## Documentation and Audit Requirements

Each accepted change MUST update:
- ADR / decision log entry
- relevant spec file(s)
- parity tests/vectors if semantics are affected
- migration notes (if applicable)
