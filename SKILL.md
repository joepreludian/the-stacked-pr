---
name: the-stacked-pr
description: Sizes the work in a spec and splits it into small, self-contained pull requests — stacked only where one depends on another — then carries that split through planning, branching, and a final PR report. Use this whenever a spec or design doc is being written (superpowers:brainstorming, bigspec sub-specs, or any "write the spec / design doc" request) — if work needs a spec it may need more than one PR, so measure it every time, even when nobody mentions PRs. Also use it when turning such a spec into a plan (superpowers:writing-plans), when implementing a plan whose spec has a "PR Stack" section, when finishing a branch and it is time to push or open PRs (superpowers:finishing-a-development-branch), and whenever the user mentions stacked PRs, splitting a big change into reviewable PRs, a PR that is too large to review, the order to open or merge PRs in, or opening PRs without the `gh` CLI or without push access.
---

# The Stacked PR

A reviewer can give a few hundred lines their full attention. Past that, review turns into skimming, and problems get approved because nobody could hold the whole change in their head. The cheapest moment to decide how work divides into pull requests is while the spec is being written, before any code exists: splitting afterwards means untangling commits that were never meant to stand alone.

This skill makes the split part of the spec, keeps the build faithful to it, and ends with a report the user can act on, including when they have no `gh` CLI or no permission to push.

It adds to the superpowers flow. It never replaces a step or skips an approval gate.

| Moment | Superpowers skill | What this skill adds |
|---|---|---|
| Spec is written | `brainstorming` | Phase 1: estimate the effort, write a `## PR Stack` section into the spec |
| Plan is written, work is built | `writing-plans`, then `subagent-driven-development` or `executing-plans` | Phase 2: group tasks by PR, one branch per PR |
| Work is done | `finishing-a-development-branch` | Phase 3: open the PRs or explain how to, then write the report |

If the spec already has a `## PR Stack` section, start at the phase that matches where the work is.

## What every PR must be

Two rules, in this order. When they pull against each other, the first one wins.

### 1. Self-contained

Someone may merge a PR and then stop: the next one gets delayed, reworked, or dropped. So each PR, merged with only the PRs it is based on, has to leave the product complete and working. A PR is self-contained when all of these hold:

- **It builds and the whole test suite passes**, with no test skipped or marked as expected to fail "until the next PR".
- **It needs nothing from a later PR.** Nothing it adds calls, imports or links to code that only arrives further up the stack.
- **Nothing a user can reach is half-built.** No button without its endpoint, no screen without its data, no email linking to a page that does not exist yet. Behaviour that is not finished is either absent, or unreachable: behind a flag that is off, not routed, not linked, not scheduled.
- **It breaks nothing that already works.** A changed signature, schema, or shared component comes with every caller updated in the same PR.
- **Data changes are safe for the code already running.** Add before use (a new table or nullable column lands before the code that reads it) and remove only after nothing reads it.

Finished code that nothing calls yet is fine: a model with tests and no callers is complete, and its callers arrive later. Stubs, `TODO` bodies, placeholder returns and commented-out halves are not: they are unfinished code on the base branch.

### 2. Small enough to review

Aim for about **400 review-relevant lines per PR**, added plus removed.

*Review-relevant* means lines a developer has to read carefully to judge the change: handwritten production code, configuration, schemas, hand-written migrations, templates, build and CI definitions.

Not counted:

- tests, fixtures, mocks and snapshots
- lockfiles
- generated and vendored code
- prose documentation, including the spec and plan
- binary assets

Tests are left out because they are read differently, mostly for what they cover, and counting them would penalise thorough testing. They still ship in the same PR as the code they cover.

The budget is a target for good judgment, not a wall. If the project or the user sets a different number (in CLAUDE.md, in the conversation, or in the spec), use theirs.

## Phase 1 — Size and slice

Do this when the design has been approved and the spec file is being written, so the split is in the document the user reviews. In `brainstorming` terms: while writing the design doc, before the spec self-review and the user review gate.

1. **List the units of change.** Go through the design and name each thing that will be created or modified: modules, endpoints, tables, screens, jobs.
2. **Estimate review-relevant lines for each unit.** Anchor on the repository whenever you can: find the closest existing equivalent and measure it (`wc -l` on a comparable handler, component, or migration). An estimate anchored on real code is far better than a guess, and it only takes a moment. Round to the nearest 50 and do not pretend to more precision than that.
3. **Decide whether a split is needed.** Estimates made before the code exists run low, because validation, error handling and wiring only show up once the code is written. So leave headroom: treat a total above about three quarters of the budget (300 lines against 400) as over it, and split wherever there is a clean seam. A single PR is right when the total sits comfortably under that, or when the change has no seam that would leave both halves self-contained.
4. **Slice it** using the principles below, aiming each slice at about three quarters of the budget for the same reason.
5. **Check every slice against the self-contained rule.** For each one, write down why merging it alone is safe. If you cannot, the slice is cut in the wrong place: move the boundary, reorder, or put the unfinished behaviour out of reach.
6. **Write the `## PR Stack` section** into the spec, using the format below.
7. **Mention it at the review gate.** When asking the user to review the spec, say how the spec proposes to divide the work into PRs, so they know to look at it. The split is theirs to change.

### Slicing principles

- **Slice by behaviour, not by layer.** "Invite API" is a slice a reviewer can reason about; "all the models" is not, because the models make no sense without their callers. A slice that cuts vertically through the layers can be verified on its own.
- **Foundations first.** Schema, shared types and interfaces come before the code that uses them.
- **Order by what users can reach.** Whatever exposes a behaviour to users (a link, a button, a scheduled job, an outgoing email) comes after everything that behaviour needs, or in the same PR.
- **Mechanical changes travel alone.** Renames, file moves, formatting and codemods bury the real change when mixed in. Give them their own PR, label it *mechanical*, and let it exceed the budget: a reviewer skims it rather than reads it.
- **Do not split what cannot stand apart.** If two pieces only work together, they are one PR. When that PR ends up over budget, keep it whole and say why in the spec. An honest 550-line PR is better than two that each need the other.
- **Do not over-split.** A slice under roughly 50 lines usually belongs with a neighbour, unless it is mechanical or risky enough to deserve separate scrutiny.

### Choosing each PR's base

Base each PR on the base branch unless it needs code from another PR in the stack. Only then does it stack on that PR. Independent PRs can be reviewed and merged in any order, so a slow review on one does not block the others.

A branch has exactly one base. When a PR needs two others that are independent of each other, put those two in a line (the second based on the first) so the third can sit on top of both.

Keep stacks shallow. More than three or four levels deep means every change near the bottom has to be carried up through all of them, so look again for slices that can be made independent.

### The spec section

Always use the heading `## PR Stack`, because the later phases look for it.

For work that fits in one PR, the whole section is:

```markdown
## PR Stack

Single PR: about 150 review-relevant lines, well within the 400-line budget.
```

For anything larger:

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
- **Delivers:** what exists or works once this merges
- **Touches:** the modules or files involved
- **Reviewer focus:** the one or two decisions that deserve scrutiny
- **Verify:** how to check this PR on its own
- **Safe alone because:** why merging only this PR leaves the product complete and working

### PR 2 — …
```

Number the PRs so that every PR comes after its base. The numbering is then also the order to open them in.

"Safe alone because" is the self-contained rule made visible. Write a specific reason ("nothing calls the model yet, and the migration only adds a table"), never a general one ("it is independent").

Name branches `<topic>/<n>-<slug>` unless the repository already has a branch naming convention, in which case follow it.

For worked examples and hard cases (a refactor that must come first, a change that resists splitting, a PR that would expose something unfinished, a migration with a backfill), read `references/slicing.md`.

## Phase 2 — Plan and build along the stack

**In the plan.** When `writing-plans` turns the spec into tasks, group the tasks under one heading per PR (`## PR 1 — Add invites table and model`), in stack order. Each task belongs to exactly one PR. A task that seems to straddle two is a sign that either the task or the split is wrong, so fix whichever it is before going on. End each PR's group with a checkpoint task: run the full test suite on that branch and measure the PR.

**Branches.** Start each PR's branch from its base (the base branch, or the parent PR's branch) just before that PR's first task, and commit that PR's tasks only there. When work is handed to subagents, tell each one which branch it is on. The spec and plan commits ride with the first PR.

**Measuring.** At each checkpoint, run:

```bash
python3 <skill-dir>/scripts/pr_size.py <base> <branch>
```

It reports review-relevant lines against the budget and shows what it left out and why. Use `--budget N` for a different budget, and `--exclude GLOB` or `--include GLOB` when it classifies a file wrongly for this project.

**When reality disagrees with the estimate.** A PR that lands somewhat over is fine. A PR heading for well past the budget (say 600 lines against 400) deserves a pause: tell the user, propose a new split, and update the `## PR Stack` section so the spec stays true. Do not let a PR grow quietly, because the reviewer was promised something they can read.

**Keeping each PR self-contained while building.** The pressure to break the rule comes mid-build: a test that needs the next PR's code, a call to a function that does not exist yet. Do not leave a stub or a skipped test behind. Either the piece belongs in this PR, or the thing that needs it belongs in the next one.

**Changing an earlier PR after later ones exist.** Commit the fix on the branch it belongs to, then bring every branch above it up to date. Before anything is pushed, `git rebase --update-refs` from the top of the stack moves them all at once. After branches are pushed, rebasing means force-pushing, which is the user's call: ask, or merge the parent into each child instead.

## Phase 3 — Publish and report

Do this when the implementation is complete. If `finishing-a-development-branch` is in play, this phase is what "push and create a Pull Request" means for a stack. A user who chooses to merge locally or to keep the branches still gets the report.

The steps assume GitHub. `references/publishing.md` has a short note for other forges.

1. **Verify each PR alone.** Check out each branch and run the full test suite there. A branch contains its parents, so a green run proves the PR works with exactly the PRs it is based on. Measure each branch with `pr_size.py`.
2. **Verify the PRs together.** Branches that are independent of each other have never run in the same tree. Merge them in a throwaway worktree and run the suite once, as described in `references/publishing.md`. A conflict or a failure there means two PRs are not as independent as the spec says: tell the user before publishing anything.
3. **Work out the order from the branches.** Run:

   ```bash
   python3 <skill-dir>/scripts/stack_plan.py <base-branch> --prefix <topic>/
   ```

   (or list the branches instead of `--prefix`). It reads the branch graph and prints two Markdown blocks: **Create the PRs in this order** (step, head branch, base to select, link) and **Merge the PRs in this order** (each merge, which PRs to re-point after it, and the exact commands if it was a squash merge).

   Order is where stacks go wrong, and a base written from memory can be wrong. This output comes from git, so it is the source for every base, every command and both order blocks from here on. If it disagrees with the spec's `## PR Stack` table, or it reports a problem, stop and tell the user: a branch was started from the wrong place, or the spec is out of date.
4. **Check what is possible.** Run:

   ```bash
   bash <skill-dir>/scripts/check_publish.sh [remote]
   ```

   It checks for a remote, push access, and an authenticated `gh`, and prints a verdict:

   | Verdict | Meaning | What to do |
   |---|---|---|
   | `auto` | Push works and `gh` is authenticated | Push and open the PRs |
   | `push-only` | Push works, but no usable `gh` | Push the branches, and hand the user the creation steps |
   | `manual` | No remote or no push access | Push nothing, and hand the user the creation steps |

5. **Ask once before anything leaves the machine.** Pushing and opening PRs is visible to other people and hard to take back. Show the list of branches, bases and PR titles in creation order, and ask for one confirmation covering the whole stack. If the user declines, treat it as `manual`.
6. **Publish in creation order**, following `references/publishing.md` for the exact commands for each verdict. Each PR is opened against the base `stack_plan.py` gave for it.
7. **Write the report**, using the template in `references/publishing.md`.
8. **Read the report back before finishing.** Without `gh`, this document is the only thing standing between the user and a stack opened in the wrong order. Confirm that:
   - every PR appears exactly once in the creation steps, with its step number, head branch, base and a way to open it that needs no `gh`;
   - every PR appears in the merge steps, and every PR that has others stacked on it says what to do to them afterwards;
   - every base in the report matches `stack_plan.py`;
   - the two order sections come before the PR details, where the user will see them first.

A failed probe is not an error to fix. Do not install `gh`, change the user's credentials, or retry with force. Missing tools or permissions are the situation the manual path exists for.

### The report

Save it to `docs/superpowers/reports/YYYY-MM-DD-<topic>-pr-stack.md` and show it in the conversation. Leave the file uncommitted, because it describes the branches and is not part of any of them.

The report leads with the order. When `gh` cannot create the PRs, the user will create and merge them by hand from this document, and nothing on GitHub will stop them doing it in the wrong order or against the wrong base. In this order, it contains:

1. **Status and a summary table**: each PR with its branch, base, actual review-relevant lines, test result, and status (opened with its URL, pushed, or local only). One line on how the PRs were verified, alone and merged together.
2. **Before you start**, only when something blocks the user: signing in, getting access, adding a remote.
3. **Create the PRs in this order**: the block from `stack_plan.py`, with each PR's title added to its row. One row per PR: step, title, head branch, base to select, link. When `gh` already created them, keep the table and put each PR's URL in place of the link, so the order and bases are still on record.
4. **Merge the PRs in this order**: the block from `stack_plan.py`, unchanged apart from adding titles. It says which PR merges when, which PRs to re-point after each merge, and the commands to run if the merge was a squash.
5. **PR details**: a title and body for every PR, in creation order, ready to paste. Each body says what the PR delivers, why it is safe to merge alone, what to focus on, how to verify it, and where it sits in the stack.
6. **Differences from the spec's plan**: PRs that were re-sliced or ended over budget, and why.
7. **More on handling a stack on GitHub**: the short tips from `references/publishing.md`.

Write it for someone who has never handled a stack. The usual mistake is opening every PR against the default branch, which makes each stacked PR show its parents' changes too. That is why the base is in every row, every time.
