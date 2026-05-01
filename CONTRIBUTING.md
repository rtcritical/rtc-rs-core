# Contributing

## Branching policy

- Do not push directly to `main`.
- Create a feature branch for every change.
- Open a pull request into `main`.

## Required checks

- `ci` must pass.
- Branch must be up to date with `main` before merge.
- At least 1 approving review is required.
- Code owner review is required.

## Local validation

- `cargo test --tests`
- `./scripts/check_changelog.sh`

## Release flow

- Tag releases as `v*` (example: `v0.1.2`).
- Release workflow publishes source/header artifacts and checksums.
- Release notes are generated pre-publish and must pass category/assignment guards.
- For v0 branch of work, treat scope as feature-frozen; prefer fixes/hardening/docs unless explicitly re-opening scope.

## API lifecycle guidance

- Follow `docs/api-lifecycle-v1.md` for additive vs breaking change handling.
- Treat `include/core_v0.h` as stable ABI line; breaking changes require explicit versioned transition planning.
