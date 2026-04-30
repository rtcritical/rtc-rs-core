#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RUSTFLAGS="${RUSTFLAGS:-}" cargo run --release --quiet --bin perf_baseline
