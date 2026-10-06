#!/usr/bin/env bash
# Check whether this repository's branches can be pushed and PRs opened
# from the command line. Changes nothing: the push check is a dry run.
#
# Usage: check_publish.sh [remote]      (remote defaults to "origin")
#
# Prints key=value lines, ending with:
#   verdict=auto        push works and gh is authenticated: push and open PRs
#   verdict=push-only   push works, no usable gh: push, then open PRs in the browser
#   verdict=manual      cannot push: give the user instructions
#   reason=...          why, in plain words
#
# The push check is best effort. A real push can still be rejected by branch
# protection rules, which a dry run cannot see.

set -u

remote="${1:-origin}"
say() { printf '%s=%s\n' "$1" "$2"; }
finish() { say verdict "$1"; say reason "$2"; exit 0; }

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  say git_repo no
  finish manual "not a git repository"
fi
say git_repo yes
say current_branch "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"

url="$(git remote get-url "$remote" 2>/dev/null || true)"
if [ -z "$url" ]; then
  say remote none
  say gh_installed "$(command -v gh >/dev/null 2>&1 && echo yes || echo no)"
  finish manual "no remote named $remote"
fi
say remote "$remote"

# Reduce the URL to host/owner/repo. Any credentials embedded in the URL are dropped
# and never printed.
case "$url" in
  /*|./*|../*|file://*)
    say host local
    say forge unknown
    say gh_installed "$(command -v gh >/dev/null 2>&1 && echo yes || echo no)"
    if git push --dry-run "$remote" "HEAD:refs/heads/stacked-pr-probe-$$" >/dev/null 2>&1; then
      say push_access yes
      finish push-only "push works; the remote is a local path, so there is no forge to open PRs on"
    fi
    say push_access no
    finish manual "cannot push to the local remote"
    ;;
esac

path="$url"
path="${path#*://}"          # scheme
path="${path#*@}"            # user or token
path="${path%.git}"
path="${path%/}"
host="${path%%[:/]*}"
rest="${path#*[:/]}"
case "$rest" in [0-9]*/*) case "${rest%%/*}" in *[!0-9]*) ;; *) rest="${rest#*/}" ;; esac ;; esac  # ssh port
repo="${rest##*/}"
owner="${rest%/*}"
say host "$host"
say owner "$owner"
say repo "$repo"

case "$host" in
  *github*) forge=github ;;
  *gitlab*) forge=gitlab ;;
  *bitbucket*) forge=bitbucket ;;
  *) forge=unknown ;;
esac
say forge "$forge"

# Dry-run push of a throwaway ref name. Never prompts: a prompt would hang the session.
ssh_cmd="${GIT_SSH_COMMAND:-$(git config --get core.sshCommand 2>/dev/null || echo ssh)}"
push_out="$(
  GIT_TERMINAL_PROMPT=0 \
  GIT_SSH_COMMAND="$ssh_cmd -o BatchMode=yes -o ConnectTimeout=10" \
  git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 \
    push --dry-run "$remote" "HEAD:refs/heads/stacked-pr-probe-$$" 2>&1
)"
push_status=$?
push_out="$(printf '%s\n' "$push_out" | sed -E 's#(://)[^/@[:space:]]+@#\1#g')"

gh_installed=no
gh_authenticated=no
if command -v gh >/dev/null 2>&1; then
  gh_installed=yes
  if gh auth status --hostname "$host" >/dev/null 2>&1; then
    gh_authenticated=yes
  fi
fi
say gh_installed "$gh_installed"
say gh_authenticated "$gh_authenticated"

if [ "$push_status" -ne 0 ]; then
  say push_access no
  detail="$(printf '%s\n' "$push_out" | grep -v '^$' | grep -iE 'denied|permission|403|401|authenticat|could not read|not found|unable|fatal|error' | head -1)"
  [ -z "$detail" ] && detail="$(printf '%s\n' "$push_out" | grep -v '^$' | tail -1)"
  case "$push_out" in
    *"publickey"*|*"could not read"*|*"Authentication failed"*|*" 401"*) why="not authenticated with $host" ;;
    *"Permission"*denied*|*" 403"*|*"not allowed"*) why="no permission to push to $remote" ;;
    *"not found"*|*"does not appear to be a git repository"*) why="remote repository not found, or no access to it" ;;
    *"Could not resolve host"*|*"timed out"*|*"Connection refused"*) why="cannot reach $host" ;;
    *) why="push check failed" ;;
  esac
  say push_detail "$detail"
  finish manual "$why"
fi
say push_access yes

if [ "$forge" = github ] && [ "$gh_authenticated" = yes ]; then
  finish auto "push works and gh is authenticated"
elif [ "$forge" = unknown ]; then
  finish push-only "push works; forge not recognised, so PRs are opened in its web interface"
elif [ "$forge" != github ]; then
  finish push-only "push works; $forge is not handled by gh"
elif [ "$gh_installed" = no ]; then
  finish push-only "push works; gh is not installed"
else
  finish push-only "push works; gh is not authenticated for $host"
fi
