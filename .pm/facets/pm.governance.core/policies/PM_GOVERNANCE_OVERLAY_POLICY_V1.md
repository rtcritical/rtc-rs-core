# PM Governance Overlay Policy (V1)

## Purpose
Provide facet-owned governance policy overlays that extend the kernel PM operations baseline without changing kernel invariants.

## Overlay scope
This governance facet overlay may define:
- governance change-control conventions
- review/approval expectations for governance-sensitive updates
- domain-specific policy defaults that remain compatible with kernel baseline

## Constraints
- Must not bypass kernel trust/provenance/validation gates.
- Must not redefine kernel invariant semantics.
- Must remain compatible with `pm.governance.core` facet lifecycle + resolver contracts.

## Precedence
1. Kernel invariants and baseline policy/procedure floor
2. Active governance facet overlay policy
3. Project-local notes that do not violate (1)

## Evidence expectations
Governance policy changes through this overlay should include:
- decision/open-question artifact
- task evidence refs
- validation output references
