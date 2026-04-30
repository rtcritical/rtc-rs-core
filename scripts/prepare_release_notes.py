#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL_CFG = ROOT / ".github" / "release.yml"
OUT = ROOT / "dist" / "release_notes.md"


def run(cmd):
    return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()


def run_optional(cmd):
    try:
        return run(cmd)
    except subprocess.CalledProcessError:
        return None


def parse_categories(path: Path):
    cats = []
    in_changelog = False
    in_categories = False
    cur = None
    in_labels = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
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
            cur["labels"].append(s[1:].strip().strip('"').lower())
        elif s and not s.startswith("-") and not s.startswith("labels:") and cur is not None:
            in_labels = False
    if cur:
        cats.append(cur)
    return cats


def infer_repo_slug():
    url = run(["git", "remote", "get-url", "origin"])
    m = re.search(r"github\.com[:/]+([^/]+)/([^/.]+)(?:\.git)?$", url)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}"


def gh_get_pr(repo_slug, pr_num, token):
    url = f"https://api.github.com/repos/{repo_slug}/pulls/{pr_num}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read().decode())
    return {
        "number": data.get("number"),
        "title": (data.get("title") or "").strip(),
        "html_url": data.get("html_url"),
        "labels": [x.get("name", "").lower() for x in data.get("labels", [])],
    }


def category_for_labels(labels, categories):
    s = set(labels)
    for c in categories:
        ls = c["labels"]
        if "*" in ls:
            continue
        if any(lbl in s for lbl in ls):
            return c["title"]
    for c in categories:
        if "*" in c["labels"]:
            return c["title"]
    return "Other Changes"


def build_fallback_bullet(subject: str):
    pr = re.search(r"#(\d+)", subject)
    if pr:
        return f"{subject} (#{pr.group(1)})"
    return subject


def main():
    cats = parse_categories(REL_CFG)
    if not cats:
        print("No categories parsed", file=sys.stderr)
        sys.exit(1)

    prev_tag = run_optional(["git", "describe", "--tags", "--abbrev=0", "HEAD^"])
    head = run(["git", "rev-parse", "--short", "HEAD"])

    log_range = f"{prev_tag}..HEAD" if prev_tag else "HEAD"
    merges = run(["git", "log", "--merges", "--pretty=%s", log_range])
    lines = [x.strip() for x in merges.splitlines() if x.strip()]

    token = os.getenv("GITHUB_TOKEN")
    repo_slug = infer_repo_slug()

    buckets = {c["title"]: [] for c in cats}

    for subject in lines:
        pr_match = re.search(r"#(\d+)", subject)
        pr_num = pr_match.group(1) if pr_match else None

        pr_meta = None
        labels = []
        if token and repo_slug and pr_num:
            try:
                pr_meta = gh_get_pr(repo_slug, pr_num, token)
                labels = pr_meta["labels"]
            except Exception:
                pr_meta = None
                labels = []

        title = category_for_labels(labels, cats)
        if not labels:
            l = subject.lower()
            if "docs" in l:
                title = next((c["title"] for c in cats if "docs" in c["labels"]), title)
            elif "fix" in l or "bug" in l:
                title = next((c["title"] for c in cats if "fix" in c["labels"] or "bug" in c["labels"]), title)
            elif "feat" in l or "enh" in l or "feature" in l:
                title = next((c["title"] for c in cats if "feature" in c["labels"] or "enhancement" in c["labels"]), title)

        if pr_meta and pr_meta.get("title") and pr_meta.get("number"):
            bullet = f"{pr_meta['title']} (#{pr_meta['number']})"
        else:
            bullet = build_fallback_bullet(subject)

        buckets.setdefault(title, []).append(bullet)

    total_assigned = sum(len(v) for v in buckets.values())
    if lines and total_assigned == 0:
        print("Release-notes guard: merges exist but no categories received entries", file=sys.stderr)
        sys.exit(2)
    if total_assigned != len(lines):
        print(
            f"Release-notes guard: assignment mismatch (merges={len(lines)} assigned={total_assigned})",
            file=sys.stderr,
        )
        sys.exit(3)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"## Release notes ({head})\n\n")
        for c in cats:
            title = c["title"]
            f.write(f"### {title}\n")
            items = buckets.get(title, [])
            if items:
                for it in items:
                    f.write(f"- {it}\n")
            else:
                f.write("- (none)\n")
            f.write("\n")

    print(str(OUT))


if __name__ == "__main__":
    main()
