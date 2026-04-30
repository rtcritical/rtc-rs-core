#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
header = ROOT / "include" / "core_v0.h"
baseline = ROOT / "docs" / "spec" / "abi-v0-symbol-baseline.txt"

h = header.read_text(encoding="utf-8")
current = sorted(set(re.findall(r"^\s*(?!typedef\b)[A-Za-z_][A-Za-z0-9_\s\*]*\s+(rtc_[a-zA-Z0-9_]+)\s*\(", h, flags=re.MULTILINE)))

if not baseline.exists():
    print("ABI_COMPAT_BASELINE_MISSING")
    print(f"Expected baseline at: {baseline}")
    sys.exit(2)

base = [ln.strip() for ln in baseline.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]
base_set = set(base)
cur_set = set(current)

removed = sorted(base_set - cur_set)
added = sorted(cur_set - base_set)

if removed:
    print("ABI_COMPAT_FAIL: removed symbol(s) from v0 baseline")
    for fn in removed:
        print(f"  - {fn}")
    if added:
        print("ABI_COMPAT_NOTE: added symbols also detected:")
        for fn in added:
            print(f"  + {fn}")
    sys.exit(1)

print("ABI_COMPAT_OK")
if added:
    print("ABI_COMPAT_NOTE: added symbol(s) (non-breaking for v0 baseline):")
    for fn in added:
        print(f"  + {fn}")
