#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf dist
mkdir -p dist

cargo build --release

tar -czf dist/rtc-rs-core-source.tar.gz \
  --exclude .git \
  --exclude target \
  --exclude dist \
  .

mkdir -p dist/include
cp include/core_v0.h dist/include/
tar -czf dist/rtc-rs-core-headers.tar.gz -C dist include

(
  cd dist
  sha256sum rtc-rs-core-source.tar.gz rtc-rs-core-headers.tar.gz > SHA256SUMS
)

[[ -f target/release/librtc_rs_core.a ]]
[[ -s dist/rtc-rs-core-source.tar.gz ]]
[[ -s dist/rtc-rs-core-headers.tar.gz ]]
[[ -s dist/SHA256SUMS ]]

grep -q 'rtc-rs-core-source.tar.gz' dist/SHA256SUMS
grep -q 'rtc-rs-core-headers.tar.gz' dist/SHA256SUMS

echo "OK: packaging contract artifacts + checksums verified"
