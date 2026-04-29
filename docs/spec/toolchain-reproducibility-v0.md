# Toolchain Reproducibility (v0)

## Purpose
Define reproducible build/test expectations for the strict ABI reference path(s).

## Supported Reference Paths
- Path A: C-core + strict C ABI
- Path B: Rust-core + strict C ABI shim

## Baseline Requirements
1. Pin compiler/toolchain versions in CI and docs.
2. Provide one-command clean build + test for each reference path.
3. Record artifact metadata (compiler version, target triple, commit SHA).
4. Run parity vectors in CI against produced artifacts.

## Minimum CI Matrix (initial)
- Linux x86_64 (required)
- Linux arm64 (recommended)

## Required Commands (template)
- `make clean && make test` (C path)
- `cargo test` + C ABI shim tests (Rust path)
- wrapper parity suite invocation

## Repro Metadata (must capture)
- git commit
- toolchain versions
- build flags
- target platform
- test summary

## Acceptance Rule
A reference path is reproducible when two clean runs on the same pinned environment produce equivalent test outcomes and parity results.
