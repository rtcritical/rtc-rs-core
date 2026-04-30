#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL_CFG = ROOT / ".github" / "release.yml"
OUT = ROOT / "dist" / "release_notes.md"


def run(cmd):
    return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()


def parse_categories(path: Path):
    title = None
    labels = []
    cats = []
    in_changelog = False
    in_categories = False
    cur = None
    in_labels = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        s = line.strip()
        if s == "changelog:":
            in_changelog = True
            continue
        if in_changelog and s == "categories:":
            in_categories = True
            continue
        if not in_categories:
            continue
        if s.startswith("- title:"):
            if cur:
                cats.append(cur)
            cur = {"title": s.split(":", 1)[1].strip().strip('"'), "labels": []}
            in_labels = False
        elif s == "labels:":
            in_labels = True
        elif in_labels and s.startswith("-") and cur is not None:
            cur["labels"].append(s[1:].strip().strip('"'))
        elif s and not s.startswith("-") and not s.startswith("labels:") and cur is not None:
            in_labels = False
    if cur:
        cats.append(cur)
    return cats


def main():
    cats = parse_categories(REL_CFG)
    if not cats:
        print("No categories parsed", file=sys.stderr)
        sys.exit(1)

    prev_tag = run(["git", "describe", "--tags", "--abbrev=0", "HEAD^"])
    head = run(["git", "rev-parse", "--short", "HEAD"])

    log = run(["git", "log", "--merges", "--pretty=%s", f"{prev_tag}..HEAD"])
    lines = [x.strip() for x in log.splitlines() if x.strip()]

    buckets = defaultdict(list)
    for ln in lines:
        l = ln.lower()
        if "docs" in l:
            buckets["docs"].append(ln)
        elif "fix" in l or "bug" in l:
            buckets["fix"].append(ln)
        elif "feat" in l or "enh" in l or "feature" in l:
            buckets["feature"].append(ln)
        else:
            buckets["other"].append(ln)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"## Release notes ({head})\n\n")
        for cat in cats:
            title = cat["title"]
            labels = [x.lower() for x in cat["labels"]]
            if "docs" in labels:
                items = buckets["docs"]
            elif "bug" in labels or "fix" in labels:
                items = buckets["fix"]
            elif "feature" in labels or "enhancement" in labels:
                items = buckets["feature"]
            else:
                items = buckets["other"]
            f.write(f"### {title}\n")
            if items:
                for it in items:
                    f.write(f"- {it}\n")
            else:
                f.write("- (none)\n")
            f.write("\n")

    print(str(OUT))


if __name__ == "__main__":
    main()
