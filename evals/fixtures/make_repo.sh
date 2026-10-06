#!/usr/bin/env bash
# Turn a fixture source tree into a fresh git repository for one test run.
#
# Usage: make_repo.sh <webapp|cli> <destination-dir>
set -euo pipefail
fixture="$1"; dest="$2"
here="$(cd "$(dirname "$0")" && pwd)"
[ -d "$here/$fixture" ] || { echo "unknown fixture: $fixture" >&2; exit 1; }
[ -e "$dest" ] && { echo "destination exists: $dest" >&2; exit 1; }
mkdir -p "$dest"
cp -R "$here/$fixture/." "$dest/"
find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
cd "$dest"
git init -q -b main .
git config user.name "Fixture"
git config user.email "fixture@example.com"
git add -A
git commit -q -m "Initial commit"
echo "created $dest (branch main, $(git rev-list --count HEAD) commit)"
