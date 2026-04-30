#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
FMT="${1:-text}"
RUSTFLAGS="${RUSTFLAGS:-}" cargo run --release --quiet --bin perf_baseline -- "$FMT"
