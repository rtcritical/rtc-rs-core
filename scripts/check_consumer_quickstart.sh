#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cargo build --release

gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke.c target/release/librtc_rs_core.a -lpthread -ldl -lm -o /tmp/consumer_smoke
/tmp/consumer_smoke | tee /tmp/consumer_smoke.out
grep -q "consumer_smoke:ok" /tmp/consumer_smoke.out

gcc -std=c11 -Wall -Wextra -Iinclude harness/consumer_smoke_callback.c -Ltarget/release -lrtc_rs_core -lpthread -ldl -lm -o /tmp/consumer_smoke_callback
LD_LIBRARY_PATH=target/release /tmp/consumer_smoke_callback | tee /tmp/consumer_smoke_callback.out
grep -q "consumer_smoke_callback:ok" /tmp/consumer_smoke_callback.out

echo "OK: consumer quickstart static/shared smoke paths verified"
