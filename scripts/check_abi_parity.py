#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
header = ROOT / "include" / "core_v0.h"
core_rs = ROOT / "src" / "core.rs"

h = header.read_text(encoding="utf-8")
r = core_rs.read_text(encoding="utf-8")

# rtc_* function declarations in header (match declaration lines only; skip typedefs)
header_fns = set(
    re.findall(r"^\s*(?!typedef\b)[A-Za-z_][A-Za-z0-9_\s\*]*\s+(rtc_[a-zA-Z0-9_]+)\s*\(", h, flags=re.MULTILINE)
)

# exported C functions in Rust
rust_fns = set(re.findall(r'pub\s+extern\s+"C"\s+fn\s+(rtc_[a-zA-Z0-9_]+)\s*\(', r))

missing_in_rust = sorted(header_fns - rust_fns)
extra_in_rust = sorted(rust_fns - header_fns)

ok = True
if missing_in_rust:
    ok = False
    print("Missing Rust export(s) for header declaration(s):")
    for fn in missing_in_rust:
        print(f"  - {fn}")

if extra_in_rust:
    ok = False
    print("Missing header declaration(s) for Rust export(s):")
    for fn in extra_in_rust:
        print(f"  - {fn}")

if not ok:
    sys.exit(1)

print("ABI_PARITY_OK")
