#!/usr/bin/env python3
"""check_test_script_headers.py

What:
  Enforce standardized header comments for test-shell scripts.

How:
  - For test files under test-scripts/*.sh (excluding manual/*), require:
      * run_* scripts: "TEST RUNNER PURPOSE"
      * all other tests: "E2E PURPOSE" and "WHAT THIS TEST ASSERTS"

Usage:
  python3 scripts/check_test_script_headers.py [repo_root]
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    test_root = repo_root / "test-scripts"
    if not test_root.is_dir():
        print(f"INFO: test-scripts not found under {repo_root}; skipping")
        return 0

    failures: list[str] = []

    for path in sorted(test_root.rglob("*.sh")):
        rel = path.relative_to(repo_root)
        if rel.parts[:2] == ("test-scripts", "manual"):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        name = path.name

        if name.startswith("run_"):
            if "TEST RUNNER PURPOSE" not in text:
                failures.append(f"{rel}: missing header 'TEST RUNNER PURPOSE'")
            continue

        if "E2E PURPOSE" not in text:
            failures.append(f"{rel}: missing header 'E2E PURPOSE'")
        if "WHAT THIS TEST ASSERTS" not in text:
            failures.append(f"{rel}: missing header 'WHAT THIS TEST ASSERTS'")

    if failures:
        print("ERROR: test script header contract failed:")
        for msg in failures:
            print(f" - {msg}")
        print("ACTION: add standardized purpose/assertion headers to listed test scripts.")
        return 1

    print("OK: test script headers conform to contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
