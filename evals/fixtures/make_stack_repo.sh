#!/usr/bin/env bash
# Build the "finished stack" fixture: the webapp repository with the team
# invites feature already implemented as four stacked branches, ready for the
# skill's publish-and-report phase.
#
#   main
#   └─ team-invites/1-schema      spec, plan, invites table and model
#      ├─ team-invites/2-api      create, list and revoke endpoints
#      │  └─ team-invites/4-ui    Settings > Team invites section
#      └─ team-invites/3-email    invite email and the sweep that queues it
#
# The remote points at a repository that does not exist, on purpose: pushes
# must fail.
#
# Usage: make_stack_repo.sh <destination-dir>
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: make_stack_repo.sh <destination-dir>" >&2; exit 1; }
dest="$1"
here="$(cd "$(dirname "$0")" && pwd)"
patches="$here/stack-repo/patches"
[ -d "$patches" ] || { echo "missing patches: $patches" >&2; exit 1; }

# The stack's commits are dated 2026-10-01 to 2026-10-05, so date the initial commit before them.
GIT_AUTHOR_DATE="2026-09-28T09:00:00" GIT_COMMITTER_DATE="2026-09-28T09:00:00" \
  bash "$here/make_repo.sh" webapp "$dest"
cd "$dest"

# stack <branch> <base> <patch-dir>: start the branch from its base and apply its commits.
stack() {
  git checkout -q -b "$1" "$2"
  git am -q --no-gpg-sign --committer-date-is-author-date "$patches/$3"/*.patch
}

stack team-invites/1-schema main                  1-schema
stack team-invites/2-api    team-invites/1-schema 2-api
stack team-invites/3-email  team-invites/1-schema 3-email
stack team-invites/4-ui     team-invites/2-api    4-ui

git remote add origin https://github.com/teamdesk-fixture-x7/teamdesk.git

[ -z "$(git status --porcelain)" ] || { echo "working tree is not clean" >&2; exit 1; }
[ "$(git rev-parse --abbrev-ref HEAD)" = "team-invites/4-ui" ] || { echo "wrong branch checked out" >&2; exit 1; }

git --no-pager branch --list
