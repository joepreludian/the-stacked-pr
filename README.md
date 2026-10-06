# the-stacked-pr

A [Claude Code](https://claude.com/claude-code) skill that decides how work divides into pull requests while the spec is being written, keeps the build faithful to that split, and ends with a report telling you which PR to create first, which base each one takes, and how to merge them.

It is designed to work alongside the [superpowers](https://github.com/obra/superpowers) skills (`brainstorming`, `writing-plans`, `finishing-a-development-branch`). It adds to that flow and never replaces a step or skips an approval gate.

## Why

A reviewer can give a few hundred lines their full attention. Past that, review turns into skimming. The cheapest moment to split work into reviewable PRs is before any code exists, because splitting afterwards means untangling commits that were never meant to stand alone.

A stack of PRs also has an order, and that is where most people get stuck: which PR to open first, what base to pick for each, and what to do with the rest of the stack after one merges. This skill works those answers out from the branches themselves and writes them down, so they still hold when the `gh` CLI is missing or you have no permission to push.

## What it does

| Moment | Superpowers skill | What this skill adds |
|---|---|---|
| The spec is written | `brainstorming` | Estimates the effort and writes a `## PR Stack` section into the spec |
| The plan is written and the work is built | `writing-plans`, then `subagent-driven-development` or `executing-plans` | Groups plan tasks by PR and gives each PR its own branch |
| The work is done | `finishing-a-development-branch` | Opens the PRs, or explains exactly how to, and writes a report |

### The two rules for every PR

1. **Self-contained.** Merged with only the PRs it is based on, a PR leaves the product complete and working:
   - it builds and the whole test suite passes;
   - it needs nothing from a later PR;
   - nothing a user can reach is half-built;
   - it breaks nothing that already works;
   - data changes are safe for the code already running.

   This rule outranks the size budget.
2. **Small enough to review.** About 400 *review-relevant* lines per PR. Tests, lockfiles, generated or vendored code, prose docs and binary assets are not counted. Tests still ship in the same PR as the code they cover.

PRs are stacked only where one needs another's code. Everything else branches from the base branch, so a slow review on one PR does not block the rest.

### Phase 1: the `## PR Stack` section in the spec

Estimates are anchored on comparable code in your repository, rounded to the nearest 50. Because estimates made before the code exists run low, a total above about three quarters of the budget is treated as over it.

```markdown
## PR Stack

Budget: about 400 review-relevant lines per PR. Tests, lockfiles, generated files and docs are not counted.
Estimated total: about 1,000 lines, split into 4 PRs.

| # | PR | Branch | Based on | Est. lines |
|---|----|--------|----------|-----------|
| 1 | Add invites table and model | `team-invites/1-schema` | `main` | ~150 |
| 2 | Invite API endpoints | `team-invites/2-api` | PR 1 | ~300 |
| 3 | Invite email delivery | `team-invites/3-email` | PR 1 | ~250 |
| 4 | Invite management screen | `team-invites/4-ui` | PR 2 | ~300 |

Open order: 1, 2, 3, 4. Each PR is opened after the one it is based on.
Merge order: 1, then 2 and 3 in either order, then 4.

### PR 1 — Add invites table and model
- **Delivers:** …
- **Touches:** …
- **Reviewer focus:** …
- **Verify:** …
- **Safe alone because:** nothing calls the model yet, and the migration only adds a table.
```

Work that fits in one PR gets a one-line section instead ("Single PR: about 150 review-relevant lines, well within the 400-line budget") and no artificial split.

### Phase 2: building along the stack

- Plan tasks are grouped under one heading per PR, each ending with a checkpoint that runs the test suite and measures the PR.
- Each PR's branch starts from its base, and that PR's commits land only there.
- If a PR heads well past the budget, the skill pauses, proposes a new split and updates the spec.

### Phase 3: publishing and the report

Before anything is published, the skill:

1. runs the full test suite on every branch alone;
2. merges the independent branches together in a throwaway worktree and runs the suite once more, because they have never run in the same tree;
3. reads the creation order and every base from the branch graph;
4. checks whether pushing works and whether `gh` is installed and signed in.

Then it asks you once before anything leaves your machine.

| Situation | What happens |
|---|---|
| Push works and `gh` is signed in | Branches are pushed and PRs are opened, in creation order, each against its real base |
| Push works, no usable `gh` | Branches are pushed, and you get a link per PR that opens GitHub's form with the base and branch already chosen |
| No remote, no access, or not signed in | Nothing is pushed, and you get the full steps to do it yourself |

In every case a report is saved to `docs/superpowers/reports/YYYY-MM-DD-<topic>-pr-stack.md` and left uncommitted. It leads with two sections:

**Create the PRs in this order**

| Step | Title | Head branch | Base to select | Open after | Link |
|---|---|---|---|---|---|
| 1 | Add invites table and model | `team-invites/1-schema` | `main` | any time | `https://github.com/<owner>/<repo>/compare/main...team-invites/1-schema?expand=1` |
| 2 | Invite API endpoints | `team-invites/2-api` | `team-invites/1-schema` | step 1 | … |
| 3 | Invite email delivery | `team-invites/3-email` | `team-invites/1-schema` | step 1 | … |
| 4 | Invite management screen | `team-invites/4-ui` | `team-invites/2-api` | step 2 | … |

**Merge the PRs in this order**

One numbered step per PR. Under each PR that has others stacked on it, the report says which PRs to re-point to the base branch and gives the exact commands to run if the merge was a squash, with your branch names in them:

```bash
git fetch origin
old_team_invites_2_api=$(git rev-parse team-invites/2-api)
git rebase --onto origin/main team-invites/1-schema team-invites/2-api
git rebase --onto origin/main team-invites/1-schema team-invites/3-email
git rebase --onto team-invites/2-api "$old_team_invites_2_api" team-invites/4-ui
git push --force-with-lease origin team-invites/2-api team-invites/3-email team-invites/4-ui
```

After those come a ready-to-paste title and body for every PR, any differences from the spec's plan, and short tips for handling a stack on GitHub.

## Install

The skill is a directory with a `SKILL.md`. Clone it into your personal skills directory:

```bash
git clone git@github.com:joepreludian/the-stacked-pr.git ~/.claude/skills/the-stacked-pr
```

Or clone it anywhere and link it:

```bash
git clone git@github.com:joepreludian/the-stacked-pr.git
ln -s "$PWD/the-stacked-pr" ~/.claude/skills/the-stacked-pr
```

To use it in one project only, put it under that project's `.claude/skills/` instead.

### Requirements

- `git`. Updating a whole stack in one command with `git rebase --update-refs` needs git 2.38 or later; nothing else does.
- `python3` 3.9 or later, standard library only, for the two Python scripts.
- `bash`, for the publish check.
- The `gh` CLI is optional. Without it the skill gives you browser links.
- The superpowers plugin is recommended. Without it, the skill still applies whenever a spec or design doc is being written.

## Using it

There is nothing to invoke. The skill engages when a spec is being written, when a spec with a `## PR Stack` section is turned into a plan or implemented, and when it is time to open PRs. You can also ask directly:

- "Write the spec for this, and tell me how it splits into PRs."
- "This PR is too big to review. How should I split it?"
- "The implementation is done. Let's get the PRs up."
- "I don't have `gh` here. What order do I open these PRs in?"

To change the budget, say so in the conversation or add a line to your project's `CLAUDE.md`, for example: `PR budget: 250 review-relevant lines.`

The instructions for creating and merging PRs assume GitHub. GitLab and Bitbucket get the same order and bases, with a short note on how a request is opened there.

## The scripts

All three only read your repository. None of them pushes or changes a branch.

### `scripts/pr_size.py`: how big is this PR?

```bash
python3 scripts/pr_size.py <base> [<head>] [--budget N] [--exclude GLOB] [--include GLOB] [--json]
```

```
PR size: team-invites/1-schema...team-invites/2-api
  review-relevant: 83 lines (+82 -1) in 3 files | budget 400 | within budget
    +72    -0     app/handlers/invites.py
    +8     -0     app/models/membership.py
    +2     -1     app/server.py
  not counted:
    tests: 169 lines in 2 files
```

It leaves out tests, lockfiles, generated and vendored code (including files marked `linguist-generated` in `.gitattributes`), prose docs and binary files. Use `--include` or `--exclude` when it classifies a file wrongly for your project.

### `scripts/stack_plan.py`: what order, and which base?

```bash
python3 scripts/stack_plan.py <base-branch> --prefix <topic>/
python3 scripts/stack_plan.py <base-branch> <branch> [<branch> ...] [--remote origin] [--json]
```

It works out each branch's base from the commit graph (the nearest other stack branch it contains, or the base branch), orders the branches so every one comes after its base, and prints the two report sections shown above as Markdown.

It also prints a "Fix before opening PRs" note when:

- the base branch has moved since the stack was started;
- a branch has no commits of its own, or two branches point at the same commit;
- a branch is built on two branches that do not contain each other.

### `scripts/check_publish.sh`: can the PRs be created from here?

```bash
bash scripts/check_publish.sh [remote]
```

Output, abbreviated:

```
remote=origin
host=github.com
forge=github
gh_installed=no
push_access=no
verdict=manual
reason=not authenticated with github.com
```

The verdict is `auto`, `push-only` or `manual`. The push check is a dry run that never prompts, and credentials embedded in a remote URL are never printed. A dry run cannot see branch protection rules, so a real push can still be rejected.

## Repository layout

```
SKILL.md                    The skill: the two rules and the three phases
references/
  slicing.md                Worked examples and hard cases for splitting work
  publishing.md             Commands per situation, PR body and report templates, GitHub tips
scripts/
  pr_size.py                Review-relevant size of a PR
  stack_plan.py             Creation order, bases and merge steps from the branch graph
  check_publish.sh          Whether pushing and gh work
evals/
  evals.json                Three test cases with their checks
  fixtures/
    webapp/                 A small standard-library Python web app
    cli/                    A small command-line tool
    stack-repo/patches/     A finished feature as four stacked branches
    make_repo.sh            Builds a git repository from webapp/ or cli/
    make_stack_repo.sh      Builds the four-branch repository from the patches
```

## How it was tested

The skill was developed with Anthropic's `skill-creator`: each test case was run once with the skill and once without, in a fresh copy of a fixture repository, and the outputs were graded against written checks.

| Test case | With the skill | Without |
|---|---|---|
| A spec for a feature too big for one PR | 12 / 12 | 1 / 12 |
| A spec for a change that fits in one PR | 5 / 5 | 3 / 5 |
| Finished stacked branches, no `gh`, no way to push | 17 / 17 | 10 / 17 |

Read these as a development check, not a benchmark:

- each configuration ran once per test case, so there is no measure of run-to-run variation;
- some runs were graded by an independent grading agent and some by the session that wrote the skill;
- several checks pass with or without the skill, and the checks were refined between rounds;
- the skill used roughly 15% to 55% more tokens than the same task without it.

The merge commands that `stack_plan.py` prints were also checked directly, by simulating squash merges of all four fixture PRs with exactly those commands. Each stacked branch kept only its own changes and the final base branch passed its full test suite.

To build a fixture repository yourself:

```bash
bash evals/fixtures/make_repo.sh webapp /tmp/teamdesk
bash evals/fixtures/make_stack_repo.sh /tmp/teamdesk-stack
```

The stack fixture's `origin` points at a repository that does not exist, on purpose, so that pushes fail.

## Limits

- **Estimates are rough.** They are made before the code exists. Phase 2 measures the real thing and corrects the split when it is far off.
- **GitHub first.** Links, re-pointing behaviour and tips are written for GitHub.
- **Stacks across forks are awkward.** A PR's base branch has to exist in the repository that receives the PR, so a stacked PR cannot target its parent's branch from a fork. The report explains the two workable routes.
- **It does not restack for you.** After a squash merge, you run the commands the report gives you.
- **File classification is by path.** `pr_size.py` recognises tests and generated files from names and directories. Check its "not counted" list the first time you use it in a project.
- **Two paths are untested on real GitHub:** opening PRs with an authenticated `gh`, and a push refused for lack of write access. Both are covered by the instructions, but not by the test runs.
