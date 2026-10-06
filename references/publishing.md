# Publishing the stack and writing the report

Read this in Phase 3. Everything here assumes GitHub unless it says otherwise.

## Contents

- Verifying the PRs together
- The order: creation and merge
- Before publishing
- Verdict `auto`: push and open PRs with `gh`
- Verdict `push-only`: push, then open PRs in the browser
- Verdict `manual`: nothing can be pushed
- More on handling a stack on GitHub (include in every report with more than one PR)
- Other forges
- PR body template
- Report template

## Verifying the PRs together

Each branch's own test run covers that PR plus the PRs it is based on. It does not cover PRs that are independent of each other: two branches off the same parent have never run in one tree. Once everything merges they will, so check that state now.

The *leaf* branches are the ones no other branch in the stack is based on. Merging all the leaves together gives the tree the base branch will have after every PR merges. Do it in a throwaway worktree so no PR branch is touched:

```bash
check="$(mktemp -d)/stack-check"
git worktree add --detach "$check" <first-leaf-branch>
git -C "$check" merge --no-edit <other-leaf-branch> [<another-leaf-branch> ...]
(cd "$check" && <test command>)
git worktree remove --force "$check"
```

For the example stack (2 and 3 on 1, 4 on 2) the leaves are `3-email` and `4-ui`.

- **Clean merge and green suite:** record it in the report ("all four merged together: 82 tests pass").
- **Conflict:** two PRs change the same lines. Whichever merges second will need a conflict resolved. Say which two in the report, and suggest stacking one on the other if the overlap is more than trivial.
- **Suite fails only when merged:** the PRs are not independent, whatever the spec says. Stop and tell the user before publishing. The fix is usually to stack one on the other, or to move the shared piece into their common parent.

Never commit the trial merge to a PR branch.

## The order: creation and merge

Two orders matter in a stack, and both go in the report:

- **Creation order.** A PR is created after the PR it is based on, because its base branch has to exist on GitHub before a PR can be opened against it.
- **Merge order.** A PR is merged after the PR it is based on. After each merge, the PRs stacked on it have to be re-pointed at the base branch before they merge.

Do not write either from memory or from the spec. Get them from the branches:

```bash
python3 <skill-dir>/scripts/stack_plan.py <base-branch> --prefix <topic>/
python3 <skill-dir>/scripts/stack_plan.py <base-branch> <branch> [<branch> ...] [--remote origin] [--json]
```

It works out each branch's base from the commit graph (the nearest other stack branch it contains, or the base branch), orders the branches so every one comes after its base, and prints:

- **Create the PRs in this order**: one push command, then a table with step, head branch, base to select, which step it has to come after, and a GitHub link that opens the PR form with that base and branch chosen.
- **Merge the PRs in this order**: one numbered step per PR. Each says when it can merge, which PRs to re-point afterwards, and the exact `git rebase --onto` commands to run if the merge was a squash or rebase merge.

Paste both blocks into the report and add each PR's title to its rows. Leave the bases, links and commands as printed: they were computed, and the commands have the real branch names in them.

The script also checks the stack and prints a "Fix before opening PRs" note when a branch has no commits of its own, when two branches point at the same commit, or when a branch does not contain the tip of the base branch. Deal with those first.

Compare its bases with the spec's `## PR Stack` table. A difference means a branch was started from the wrong place or the spec is out of date. Tell the user which, and do not publish until they agree on the fix.

**If the team is not used to stacks,** offer the one-at-a-time alternative in the report: open only the PRs based on the base branch now, and open each child after its parent merges, with the base branch as its base. Nobody has to re-point a PR. The costs are that reviews of the later PRs start later, and that a child branch still needs the `rebase --onto` step from the merge block before it is opened if its parent was squash-merged. Give this as an option, not as the default.

## Before publishing

Have these ready for every PR, in creation order: branch, base, title, body. Write each body to a temporary file so it can be passed to a command or pasted into the report unchanged.

The confirmation in Phase 3 covers one push of the listed branches and the creation of the listed PRs. It does not cover force-pushing, pushing to the base branch, or anything not on the list.

## Verdict `auto`: push and open PRs with `gh`

Push in creation order, so every base exists on the remote when its PR is created:

```bash
git push -u <remote> <branch-1>
git push -u <remote> <branch-2>
```

Create each PR, in the same order, against its real base:

```bash
gh pr create --base <base> --head <branch> --title "<title>" --body-file <body-file>
```

For a stacked PR, `<base>` is the parent PR's branch, not the default branch. This is what makes the PR show only its own changes.

Once all PRs exist and their numbers are known, update each body so its stack table links to the others:

```bash
gh pr edit <number> --body-file <updated-body-file>
```

If a push or a `gh` call fails partway, stop. Do not retry with force. Report what was created and what was not, and write manual instructions for the remainder.

## Verdict `push-only`: push, then open PRs in the browser

Push the branches as above. Then give the user one link per PR, listed in creation order. This URL opens GitHub's "Open a pull request" form with the base and branch already chosen:

```
https://github.com/<owner>/<repo>/compare/<base>...<branch>?expand=1
```

`check_publish.sh` prints `owner`, `repo` and `host`. For short titles, the title can be prefilled by appending `&title=<url-encoded title>`. Do not put the body in the URL: long URLs get truncated. Give the body in the report for the user to paste.

The creation block from `stack_plan.py` already has these links with the right base in each. Use it as printed, and give the title and body for each PR under "PR details". Tell the user to check the base shown at the top of the form before submitting.

## Verdict `manual`: nothing can be pushed

Work out which situation applies from the `reason` line, and write instructions for that one. Do not dump all of them on the user. The situation only changes the "Before you start" section of the report. The creation and merge blocks from `stack_plan.py` go in every time, so the user has the order, the bases and the merge steps ready for the moment they can push.

### No remote

The repository has no remote. Tell the user to create the repository on GitHub, then:

```bash
git remote add origin <url>
git push -u origin <base-branch>
git push -u origin <branch-1> <branch-2> <branch-3>
```

### Remote exists, but no permission to push

Usually the user is not a collaborator on the repository. There are three ways forward. Lead with the one that fits what you know about the project.

**Ask for write access.** For a team repository this is normally the answer. Once granted, the `push-only` or `auto` steps apply as written. Give the user those steps so they are ready.

**Use a fork.** For open source, or when access will not be granted:

```bash
# After forking in the browser (or: gh repo fork --remote=false)
git remote add fork <fork-url>
git push -u fork <branch-1> <branch-2> <branch-3>
```

Explain the limitation honestly: a PR's base branch has to exist in the repository that receives the PR. The first PR, and any PR based directly on the base branch, can be opened against the upstream repository from the fork as usual:

```
https://github.com/<upstream-owner>/<repo>/compare/<base>...<fork-owner>:<branch>?expand=1
```

A stacked PR cannot target its parent's branch upstream, because that branch only exists in the fork. Offer both workable routes:

- Open the stacked PRs upstream one at a time: when the parent merges, rebase the child onto the base branch and open it then.
- Or open the stacked PRs inside the fork (base is the parent branch in the fork) so reviewers can read them now, and re-open each upstream as its parent merges.

**Hand the work to someone with access.** When neither works, the branches can travel as a single file:

```bash
git bundle create <topic>-stack.bundle <base-branch>..<branch-1> <base-branch>..<branch-2> <base-branch>..<branch-3>
```

The recipient runs `git fetch <topic>-stack.bundle '*:*'` and gets the same branches.

### Not authenticated

The remote rejected the credentials, or asked for some and none were available. Say so, and point at the fix rather than attempting it:

- HTTPS remotes need a credential helper or a personal access token.
- SSH remotes need a key registered with GitHub. `ssh -T git@github.com` tells the user whether theirs works.
- `gh auth login` sets up both `gh` and git credentials. The user can run it themselves in this session by typing `! gh auth login`.

GitHub gives the same answer for "not signed in", "no access" and "repository does not exist", so say that write access could not be confirmed, and tell the user what a failed push after signing in would mean.

### The user declined to publish

Not an error. Say the branches are local and untouched, and give the `push-only` steps so they can publish when they choose.

## More on handling a stack on GitHub

The merge block from `stack_plan.py` covers the step-by-step. Add these tips after it in every report with more than one PR, using the real branch names. Most people have not handled a stack before.

**A PR opened against the wrong base does not need closing.** Use *Edit* next to the PR title and change the base. The sign that it happened: a stacked PR shows its parent's files as well as its own.

**GitHub does not enforce the merge order.** Nothing stops someone merging PR 2 before PR 1, and doing so merges PR 2's commits into PR 1's branch, not into `main`. Two ways to prevent it:

- open the stacked PRs as drafts and mark each ready when its parent has merged, or
- put "Merge after #<parent>" as the first line of each stacked PR's description (the body template does this).

**Let GitHub re-point for you.** Turning on *Automatically delete head branches* in the repository settings means that when a parent merges, its branch is deleted and GitHub switches the PRs stacked on it to the base branch.

**Why a squash merge needs the extra commands.** After a squash, the child's branch still holds the parent's original commits, which no longer match what is on the base branch, so the child shows conflicts or duplicate changes. The `git rebase --onto` commands in the merge block move only the child's own commits onto the updated base branch. A team that merges with plain merge commits never needs them.

**Changing a PR after review.** Commit the fix on that PR's branch and push it. Then update each branch stacked on it, bottom to top:

```bash
git checkout <child-branch>
git merge <parent-branch>
git push <remote> <child-branch>
```

Merging avoids a force-push. If the team prefers a linear history, rebase instead and push with `--force-with-lease`.

**Independent PRs** (those based directly on the base branch, with nothing stacked on them) need none of this. Merge them whenever they are approved.

## Other forges

`check_publish.sh` reports `forge` as `github`, `gitlab`, `bitbucket` or `unknown`. The creation order, the bases and the self-contained rule are the same everywhere. Only the way a request is opened differs:

- **GitLab.** A push can create the merge request with no CLI: `git push -u <remote> <branch> -o merge_request.create -o merge_request.target=<base> -o merge_request.title="<title>"`.
- **Bitbucket.** `https://bitbucket.org/<owner>/<repo>/pull-requests/new?source=<branch>&dest=<base>`.
- **Unknown.** Push the branches and tell the user to open one request per branch in the web interface, naming the base for each. Most forges print a creation link in the output of `git push`. Quote it in the report when they do.

## PR body template

```markdown
<Only for a stacked PR, as the first line:> Merge after PR <n>.

## What this delivers
<One or two sentences: what works after this merges.>

## Safe to merge alone because
<The specific reason merging only this PR leaves the product complete and working.>

## Reviewer focus
<The one or two decisions that deserve the closest reading.>

## How to verify
<Commands or steps to check this PR on its own.>

## Stack
Part <n> of <total> for <topic>. Spec: `<path to spec>`

| # | PR | Based on |
|---|----|----------|
| 1 | <title, or link once opened> | `main` |
| **2** | **<this PR>** | PR 1 |
| 3 | <title, or link once opened> | PR 1 |

<Only for a stacked PR:> This diff shows only this PR's changes as long as the base is `<parent-branch>`.

Size: <n> review-relevant lines (tests, lockfiles, generated files and docs not counted).
```

Follow the repository's own PR template if it has one, and fit these sections into it.

## Report template

The two order sections are required in every report and come before the PR details. They are the `stack_plan.py` output with titles added.

```markdown
# PR Stack Report: <topic>

Spec: `<path>` · Plan: `<path>` · <date>

**Status:** <one line: "4 PRs opened", or "4 branches pushed, PRs not opened yet (gh is not installed)", or "4 branches ready locally, nothing pushed (no push access to origin)">

| # | PR | Branch | Base | Review-relevant lines | Tests | Status |
|---|----|--------|------|-----------------------|-------|--------|
| 1 | Add invites table and model | `team-invites/1-schema` | `main` | 162 | pass | Local only |
| 2 | Invite API endpoints | `team-invites/2-api` | `team-invites/1-schema` | 371 | pass | Local only |

**Verified:** each branch alone (full suite), and all PRs merged together (<result>).

## Before you start
<Only when something blocks the user: sign in, get access, add a remote. Numbered, with commands. Omit otherwise.>

## Create the PRs in this order
<From stack_plan.py: the push command, then the table, with a Title column added.>

| Step | Title | Head branch | Base to select | Open after | Link |
|---|---|---|---|---|---|
| 1 | Add invites table and model | `team-invites/1-schema` | `main` | any time | <link> |
| 2 | Invite API endpoints | `team-invites/2-api` | `team-invites/1-schema` | step 1 | <link> |

For each one: open the link, check the base shown at the top of the form matches the table, and paste the title and body from "PR details".

## Merge the PRs in this order
<From stack_plan.py, unchanged apart from titles: one numbered step per PR, with the re-point and squash-merge follow-up under each PR that has others stacked on it.>

## PR details
<For each PR, in creation order: title, base, and the full body in a fenced block so it can be copied.>

## Differences from the spec
<PRs re-sliced, added, merged or over budget, each with the reason. "None" if the stack matches the spec.>

## More on handling a stack on GitHub
<The tips above, adapted to this stack's branch names.>
```
