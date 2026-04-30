# Backlog

## Epic Mapping

| Epic ID | Goal Ref | Epic Name | Priority | Owner | Status | Completion Criteria |
|---|---|---|---|---|---|---|
| E-101 | P1 | PM governance + v1 planning baseline | P0 | Nick | done | Strict PM enforcement enabled and v1 task inventory seeded |
| E-102 | P1 | Packaging and distribution ergonomics | P1 | Nick | todo | Consumer packaging path implemented + validated |
| E-103 | P1 | Reliability and callback/error hardening | P1 | Nick | todo | Error/callback hardening slices complete with tests |
| E-104 | P1 | Release governance and automation quality | P2 | Nick | todo | Release/process governance runbook and gates hardened |

## Task List

| Task ID | Epic ID | Task | Priority | Status | Owner | Depends On | Notes |
|---|---|---|---|---|---|---|---|
| T-102 | E-102 | V1 Epic A - Packaging and distribution ergonomics | P1 | in-progress | nick | T-101 | source_note=.pm/inbox/raw/2026-04-30-v1-planning-kickoff.md; decision_ref=.pm/decisions/open-questions.yml; evidence_ref=docs/post-v0-roadmap.md; evidence_ref=docs/v0-closeout.md; risk=medium; Epic container task decomposed into T-105 (planning matrix/contract) and T-106 (packaging verification gates).; No implementation executed in this planning pass. |
| T-103 | E-103 | V1 Epic B - Reliability and callback/error hardening | P1 | in-progress | nick | T-101 | source_note=.pm/inbox/raw/2026-04-30-v1-planning-kickoff.md; decision_ref=.pm/decisions/open-questions.yml; evidence_ref=tests/abi_surface.rs; evidence_ref=harness/consumer_smoke.c; evidence_ref=harness/consumer_smoke_callback.c; risk=medium; Epic container task decomposed into T-107 (error-contract expectations/tests) and T-108 (callback lifecycle hardening).; No implementation executed in this planning pass. |
| T-109 | E-104 | V1.C1 - Release governance runbook and incident handling hardening | P2 | todo | nick | T-104 | source_note=.pm/inbox/raw/2026-04-30-v1-planning-kickoff.md; decision_ref=.pm/decisions/open-questions.yml; evidence_ref=scripts/prepare_release_notes.py; evidence_ref=.github/workflows/release.yml; risk=low; Planning+documentation slice; can precede further automation. |
| T-110 | E-104 | V1.C2 - Governance guard consistency across local hooks and CI | P2 | todo | nick | T-109 | source_note=.pm/inbox/raw/2026-04-30-v1-planning-kickoff.md; decision_ref=.pm/decisions/open-questions.yml; evidence_ref=.github/workflows/ci.yml; evidence_ref=.githooks/pre-commit; evidence_ref=.pm/policies; risk=low; Completes E-104 by making governance behavior predictable in all execution contexts. |
| T-104 | E-104 | V1 Epic C - Release governance and automation quality | P2 | in-progress | nick | T-101 | source_note=.pm/inbox/raw/2026-04-30-v1-planning-kickoff.md; decision_ref=.pm/decisions/open-questions.yml; evidence_ref=.github/workflows/ci.yml; evidence_ref=.pm/procedures/pm-operations.md; evidence_ref=scripts/prepare_release_notes.py; evidence_ref=scripts/check_abi_compat_policy.py; evidence_ref=docs/abi-compat-policy.md; evidence_ref=docs/post-v0-roadmap.md; evidence_ref=docs/spec/abi-v0-symbol-baseline.txt; risk=low; Epic container task decomposed into T-109 (release runbook/incident handling) and T-110 (local-vs-CI governance parity).; Includes ABI compatibility policy guard and post-v0 roadmap/spec baselines in this slice.; No implementation executed in this planning pass. |
| T-111 | E-104 | V1.C3 - GitHub facet configurability model (defaults + project overrides) | P2 | todo | nick | T-110 | source_note=.pm/inbox/raw/2026-04-30-v1-planning-kickoff.md; decision_ref=.pm/decisions/open-questions.yml; evidence_ref=.pm/facets/github.core/facet.yml; evidence_ref=.pm/facets/github.release-ops/facet.yml; evidence_ref=.pm/generated/pm-runtime-brief.yml; evidence_ref=.pm/policies/rtc-github-governance-policy.md; risk=medium; Requested by Nick after epic-branch CI flow policy adoption. |

## Status Vocabulary

- `todo`
- `in-progress`
- `blocked`
- `done`
