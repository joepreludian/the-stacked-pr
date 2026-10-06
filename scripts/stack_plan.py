#!/usr/bin/env python3
"""Work out a stack's creation order, bases and merge steps from its branches.

Reads the branch graph, so the answer reflects what is actually in git rather
than what a document says. Prints Markdown ready to go into the PR report:
which PR to create first, which base each one takes, and how to merge them.

Usage:
    stack_plan.py <base-branch> <branch> [<branch> ...] [--remote origin] [--json]
    stack_plan.py <base-branch> --prefix team-invites/ [--remote origin] [--json]

A branch's base is the nearest other branch in the stack that it contains, or
the base branch when it contains none of them. Changes nothing in the repository.
"""

import argparse
import json
import re
import subprocess
import sys


def run(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def git(*args):
    result = run(*args)
    if result.returncode != 0:
        sys.exit(f"stack_plan: git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def is_ancestor(older, newer):
    return run("merge-base", "--is-ancestor", older, newer).returncode == 0


def natural(name):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def github_slug(remote):
    """Return (host, owner/repo) for a GitHub remote, or None."""
    result = run("remote", "get-url", remote)
    if result.returncode != 0:
        return None
    url = result.stdout.strip()
    path = url.split("://", 1)[-1].split("@", 1)[-1]
    path = re.sub(r"\.git/?$", "", path).rstrip("/")
    match = re.match(r"^([^/:]+)[:/](?:\d+/)?(.+)$", path)
    if not match or "github" not in match.group(1):
        return None
    return match.group(1), match.group(2)


def build_plan(base, branches, remote):
    tips = {branch: git("rev-parse", "--verify", f"{branch}^{{commit}}") for branch in branches}
    base_tip = git("rev-parse", "--verify", f"{base}^{{commit}}")
    problems = []

    seen = {}
    for branch, tip in tips.items():
        if tip == base_tip:
            problems.append(f"`{branch}` has no commits of its own: it points at the same commit as `{base}`.")
        if tip in seen:
            problems.append(f"`{branch}` and `{seen[tip]}` point at the same commit, so one of them is empty.")
        seen.setdefault(tip, branch)

    # Bases come from ancestry alone. Counting commits with `a..b` can give wrong
    # answers when commit dates are out of order, which rebased stacks often have.
    parent, behind = {}, []
    for branch in sorted(branches, key=natural):
        inside = [
            other for other in branches
            if other != branch and tips[other] != tips[branch] and is_ancestor(other, branch)
        ]
        nearest = sorted(
            (c for c in inside if not any(o != c and is_ancestor(c, o) for o in inside)), key=natural
        )
        parent[branch] = nearest[0] if nearest else base
        if len(nearest) > 1:
            names = " and ".join(f"`{name}`" for name in nearest)
            problems.append(
                f"`{branch}` contains {names}, which do not contain each other. A PR has one base, "
                f"so stack one of those on the other first."
            )
        if parent[branch] == base and not is_ancestor(base, branch):
            behind.append(branch)
    if behind:
        names = ", ".join(f"`{name}`" for name in behind)
        problems.append(
            f"`{base}` has moved since the stack was started: {names} (and everything stacked on them) "
            f"do not contain its latest commit. Update the stack onto `{base}` before opening PRs."
        )

    ordered, pending = [], sorted(branches, key=natural)
    while pending:
        ready = [branch for branch in pending if parent[branch] == base or parent[branch] in ordered]
        if not ready:  # cannot happen with a real commit graph; guard against a loop anyway
            sys.exit("stack_plan: could not order the branches")
        ordered.append(ready[0])
        pending.remove(ready[0])

    step = {branch: index for index, branch in enumerate(ordered, start=1)}
    slug = github_slug(remote)
    rows = []
    for branch in ordered:
        url = None
        if slug:
            url = f"https://{slug[0]}/{slug[1]}/compare/{parent[branch]}...{branch}?expand=1"
        rows.append({
            "step": step[branch],
            "branch": branch,
            "base": parent[branch],
            "needs_step": step.get(parent[branch]),
            "children": [other for other in ordered if parent[other] == branch],
            "open_url": url,
        })
    return {"base_branch": base, "remote": remote, "github": bool(slug), "prs": rows, "problems": problems}


def descendants(plan, branch):
    """Branches stacked on `branch`, parents before children."""
    by_branch = {row["branch"]: row for row in plan["prs"]}
    found, queue = [], list(by_branch[branch]["children"])
    while queue:
        current = queue.pop(0)
        found.append(current)
        queue.extend(by_branch[current]["children"])
    return found


def shell_name(branch):
    return "old_" + re.sub(r"\W+", "_", branch).strip("_")


def rebase_commands(plan, merged):
    """Commands to run after `merged` lands as a squash or rebase merge."""
    by_branch = {row["branch"]: row for row in plan["prs"]}
    base, remote = plan["base_branch"], plan["remote"]
    moved = descendants(plan, merged)
    lines = [f"git fetch {remote}"]
    for branch in moved:
        row = by_branch[branch]
        if row["children"]:
            lines.append(f"{shell_name(branch)}=$(git rev-parse {branch})")
        if row["base"] == merged:
            lines.append(f"git rebase --onto {remote}/{base} {merged} {branch}")
        else:
            lines.append(f'git rebase --onto {row["base"]} "${shell_name(row["base"])}" {branch}')
    lines.append(f"git push --force-with-lease {remote} " + " ".join(moved))
    return lines


def render(plan):
    base, remote, prs = plan["base_branch"], plan["remote"], plan["prs"]
    out = []
    if plan["problems"]:
        out += ["> **Fix before opening PRs:**"] + [f"> - {problem}" for problem in plan["problems"]] + [""]

    out += [
        "## Create the PRs in this order",
        "",
        "A PR can only be opened once its base branch is on GitHub, so push every branch first, "
        "then open the PRs from step 1 down. Each PR is opened against the base in its row. "
        f"Only the rows that say `{base}` use `{base}`.",
        "",
        "```bash",
        f"git push -u {remote} " + " ".join(row["branch"] for row in prs),
        "```",
        "",
        "| Step | Head branch | Base to select | Open after | Link |",
        "|---|---|---|---|---|",
    ]
    for row in prs:
        after = f"step {row['needs_step']}" if row["needs_step"] else "any time"
        link = row["open_url"] or "open in the web interface"
        out.append(f"| {row['step']} | `{row['branch']}` | `{row['base']}` | {after} | {link} |")

    swaps = {}
    for row in prs:
        swaps.setdefault(row["base"], []).append(row["step"])
    for steps in swaps.values():
        if len(steps) > 1:
            out += ["", f"Steps {' and '.join(map(str, steps))} have the same base and can be opened in either order."]

    out += ["", "## Merge the PRs in this order", ""]
    out.append(
        "Merge a PR only when the PR it was based on has merged. After each merge, do the "
        "follow-up listed under it before merging anything stacked on it."
    )
    out.append("")
    for row in prs:
        needs = f"after step {row['needs_step']}" if row["needs_step"] else "first, or at any time"
        out.append(f"{row['step']}. **Merge `{row['branch']}`** ({needs}). By then its base is `{base}`.")
        if not row["children"]:
            out.append("   - Nothing is stacked on it, so there is no follow-up.")
            continue
        kids = ", ".join(f"`{child}`" for child in row["children"])
        out.append(
            f"   - **Re-point:** {kids} had `{row['branch']}` as base and must now target `{base}`. "
            f"GitHub does this by itself when `{row['branch']}` is deleted on merge. Otherwise open each "
            f"of those PRs, choose *Edit* next to the title, and set the base to `{base}`."
        )
        out.append("   - **Only if this merge was a squash or rebase merge,** also run:")
        out.append("     ```bash")
        out += [f"     {line}" for line in rebase_commands(plan, row["branch"])]
        out.append("     ```")
        out.append(
            "     A plain merge commit needs none of this. The force-push rewrites only the stacked "
            "branches, which is expected."
        )
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Creation order, bases and merge steps for a stack.")
    parser.add_argument("base", help="the branch the stack starts from, e.g. main")
    parser.add_argument("branches", nargs="*", help="the PR branches, in any order")
    parser.add_argument("--prefix", help="use every local branch starting with this prefix")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    branches = list(args.branches)
    if args.prefix:
        listed = git("for-each-ref", "--format=%(refname:short)", f"refs/heads/{args.prefix}*")
        branches += [name for name in listed.splitlines() if name and name not in branches]
    if not branches:
        parser.error("give the PR branches, or --prefix")
    if args.base in branches:
        parser.error("the base branch cannot also be one of the PR branches")

    plan = build_plan(args.base, branches, args.remote)
    print(json.dumps(plan, indent=2) if args.json else render(plan))


if __name__ == "__main__":
    main()
