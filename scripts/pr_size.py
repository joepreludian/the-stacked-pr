#!/usr/bin/env python3
"""Measure a PR's review-relevant size.

Counts added + removed lines between <base> and <head> (from their merge base),
leaving out files a reviewer does not need to read line by line: tests,
lockfiles, generated or vendored code, prose docs, and binary assets.

Usage:
    pr_size.py <base> [<head>] [--budget N] [--exclude GLOB]... [--include GLOB]... [--json]

    <head> defaults to HEAD.
    --exclude GLOB   also leave out paths matching GLOB (repeatable)
    --include GLOB   count paths matching GLOB even if a built-in rule
                     would leave them out (repeatable, wins over --exclude)

Exit status is 0 whether or not the PR is within budget; being over budget is
information for a judgment call, not a failure.
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import PurePosixPath

DEFAULT_BUDGET = 400

TEST_DIRS = {
    "test", "tests", "__tests__", "spec", "specs", "e2e", "testdata",
    "fixtures", "__fixtures__", "mocks", "__mocks__", "__snapshots__",
    "cypress", "playwright", "testing",
}
TEST_FILE_GLOBS = [
    "test_*.py", "*_test.py", "conftest.py", "*_test.go", "*_test.rs",
    "*.test.*", "*.spec.*", "*_spec.rb", "*_test.rb", "*Test.java",
    "*Tests.java", "*Test.kt", "*Tests.kt", "*Test.cs", "*Tests.cs",
    "*Tests.swift", "*Test.php", "*_test.exs", "*_test.dart", "*.snap",
    "*.stories.*",
]
LOCKFILES = {
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
    "bun.lock", "bun.lockb", "cargo.lock", "poetry.lock", "uv.lock",
    "pipfile.lock", "pdm.lock", "gemfile.lock", "composer.lock", "go.sum",
    "flake.lock", "mix.lock", "podfile.lock", "packages.lock.json",
    "pubspec.lock", "gradle.lockfile", "package.resolved",
}
GENERATED_DIRS = {
    "node_modules", "vendor", "third_party", "dist", "build", "generated",
    "__generated__", ".next", "target", "coverage",
}
GENERATED_FILE_GLOBS = [
    "*.min.js", "*.min.css", "*.map", "*.pb.go", "*_pb2.py", "*_pb2_grpc.py",
    "*.pb.h", "*.pb.cc", "*.generated.*", "*.gen.*", "*.g.dart",
    "*.freezed.dart", "*.designer.cs",
]
DOC_EXTS = {".md", ".mdx", ".rst", ".adoc"}
DOC_NAMES = {"license", "licence", "changelog", "authors", "notice", "contributors"}
ASSET_EXTS = {".svg"}


def git(*args, stdin=None):
    result = subprocess.run(
        ["git", *args], input=stdin, capture_output=True, text=True
    )
    if result.returncode != 0:
        sys.exit(f"pr_size: git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def numstat(base, head):
    """Yield (added, removed, path, is_binary) for each changed file."""
    out = git("diff", "--numstat", "-M", "-z", f"{base}...{head}")
    fields = out.split("\0")
    i = 0
    while i < len(fields):
        entry = fields[i]
        if not entry:
            i += 1
            continue
        added, removed, path = entry.split("\t", 2)
        if path == "":
            # Rename: the old and new paths follow as separate fields.
            path = fields[i + 2]
            i += 3
        else:
            i += 1
        if added == "-":
            yield 0, 0, path, True
        else:
            yield int(added), int(removed), path, False


def linguist_generated(paths):
    """Paths the repository marks as generated in .gitattributes."""
    if not paths:
        return set()
    out = git("check-attr", "-z", "--stdin", "linguist-generated", stdin="\0".join(paths))
    fields = out.split("\0")
    marked = set()
    for i in range(0, len(fields) - 2, 3):
        path, _attr, value = fields[i : i + 3]
        if value in ("set", "true"):
            marked.add(path)
    return marked


def matches(path, name, globs):
    return any(fnmatch.fnmatch(name, g) or fnmatch.fnmatch(path, g) for g in globs)


def classify(path, is_binary, marked_generated, user_exclude, user_include):
    """Return None if the file counts, else the reason it is left out."""
    pure = PurePosixPath(path)
    name = pure.name
    lower = name.lower()
    dirs = {part.lower() for part in pure.parts[:-1]}

    if matches(path, name, user_include):
        return None
    if matches(path, name, user_exclude):
        return "excluded by option"
    if is_binary:
        return "binary"
    if lower in LOCKFILES:
        return "lockfiles"
    if path in marked_generated or dirs & GENERATED_DIRS or matches(path, name, GENERATED_FILE_GLOBS):
        return "generated or vendored"
    if pure.suffix.lower() in DOC_EXTS or pure.stem.lower() in DOC_NAMES:
        return "docs"
    if dirs & TEST_DIRS or matches(path, name, TEST_FILE_GLOBS):
        return "tests"
    if pure.suffix.lower() in ASSET_EXTS:
        return "assets"
    return None


def main():
    parser = argparse.ArgumentParser(description="Measure a PR's review-relevant size.")
    parser.add_argument("base")
    parser.add_argument("head", nargs="?", default="HEAD")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB")
    parser.add_argument("--include", action="append", default=[], metavar="GLOB")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = list(numstat(args.base, args.head))
    marked = linguist_generated([f[2] for f in files])

    counted = []
    skipped = {}
    for added, removed, path, is_binary in files:
        if not is_binary and added + removed == 0:
            continue  # renamed or mode-changed only: nothing to read
        reason = classify(path, is_binary, marked, args.exclude, args.include)
        if reason is None:
            counted.append({"path": path, "added": added, "removed": removed})
        else:
            bucket = skipped.setdefault(reason, {"lines": 0, "files": []})
            bucket["lines"] += added + removed
            bucket["files"].append(path)

    added = sum(f["added"] for f in counted)
    removed = sum(f["removed"] for f in counted)
    total = added + removed
    counted.sort(key=lambda f: f["added"] + f["removed"], reverse=True)

    if args.json:
        json.dump(
            {
                "base": args.base,
                "head": args.head,
                "budget": args.budget,
                "review_relevant_lines": total,
                "added": added,
                "removed": removed,
                "over_budget": total > args.budget,
                "counted_files": counted,
                "not_counted": skipped,
            },
            sys.stdout,
            indent=2,
        )
        print()
        return

    verdict = "within budget" if total <= args.budget else f"over budget by {total - args.budget}"
    print(f"PR size: {args.base}...{args.head}")
    print(
        f"  review-relevant: {total} lines (+{added} -{removed}) in {len(counted)} files"
        f" | budget {args.budget} | {verdict}"
    )
    for f in counted[:10]:
        print(f"    +{f['added']:<5} -{f['removed']:<5} {f['path']}")
    if len(counted) > 10:
        print(f"    ... and {len(counted) - 10} more files")
    if skipped:
        print("  not counted:")
        for reason, bucket in sorted(skipped.items()):
            print(f"    {reason}: {bucket['lines']} lines in {len(bucket['files'])} files")
    if not files:
        print("  no changes between these refs")


if __name__ == "__main__":
    main()
