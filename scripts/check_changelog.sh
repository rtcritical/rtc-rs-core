#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f CHANGELOG.md ]]; then
  echo "MISSING_CHANGELOG"
  exit 1
fi
if ! grep -q "## \[Unreleased\]" CHANGELOG.md; then
  echo "MISSING_UNRELEASED_SECTION"
  exit 1
fi
echo "CHANGELOG_OK"
