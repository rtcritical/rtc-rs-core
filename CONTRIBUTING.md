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
