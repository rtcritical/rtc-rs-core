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

# Optional prebuilt convenience artifacts (best-effort / non-blocking)
PREBUILT_ENTRIES=""
if [[ -f target/release/librtc_rs_core.a ]]; then
  cp target/release/librtc_rs_core.a dist/
  (
    cd dist
    sha256sum librtc_rs_core.a >> SHA256SUMS
  )
  PREBUILT_ENTRIES='    {"name":"librtc_rs_core.a","required":false}'
fi

cat > dist/packaging_manifest.json <<EOF
{
  "schema": "rtc.packaging.v1",
  "required": [
    {"name":"rtc-rs-core-source.tar.gz","required":true},
    {"name":"rtc-rs-core-headers.tar.gz","required":true},
    {"name":"SHA256SUMS","required":true}
  ],
  "optional_prebuilt": [
${PREBUILT_ENTRIES}
  ]
}
EOF

[[ -f target/release/librtc_rs_core.a ]]
[[ -s dist/rtc-rs-core-source.tar.gz ]]
[[ -s dist/rtc-rs-core-headers.tar.gz ]]
[[ -s dist/SHA256SUMS ]]
[[ -s dist/packaging_manifest.json ]]

grep -q 'rtc-rs-core-source.tar.gz' dist/SHA256SUMS
grep -q 'rtc-rs-core-headers.tar.gz' dist/SHA256SUMS
grep -q 'rtc-rs-core-source.tar.gz' dist/packaging_manifest.json
grep -q 'rtc-rs-core-headers.tar.gz' dist/packaging_manifest.json

echo "OK: packaging contract artifacts + checksums + manifest verified"
