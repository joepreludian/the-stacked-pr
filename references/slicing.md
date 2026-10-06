# Slicing: examples and hard cases

Read this when a split is not obvious. `SKILL.md` has the principles; this file shows them applied.

## Contents

- Estimating before code exists
- Example: a feature across API and UI
- Example: work that fits in one PR
- Hard case: a refactor has to come first
- Hard case: the change resists splitting
- Hard case: a PR would expose something unfinished
- Hard case: schema change with a backfill
- Hard case: one PR needs two independent parents
- Checking a split before writing it down

## Estimating before code exists

Estimates come from the repository, not from intuition.

1. For each unit in the design, find the closest thing that already exists: another endpoint, another form, another background job.
2. Measure it: `wc -l path/to/that/file`. Count only the files a reviewer would read carefully, not its tests.
3. Adjust for obvious differences ("ours has twice the fields", "ours has no pagination").
4. Round to the nearest 50.

In a new project with nothing to anchor on, estimate from the design itself (each endpoint, each screen, each table) and say in the spec that the numbers are rough. Phase 2 measures the real thing, so a rough estimate gets corrected early.

Modifying existing code usually costs fewer lines than adding new code, but more reviewer attention per line. Do not shave the estimate to squeeze a risky modification into a neighbouring PR.

Expect the real number to come in higher. Anchors measure the happy path of code someone already tidied; new code brings validation, error cases and wiring that the design did not spell out. One feature estimated this way at 400 lines measured 476 once built. That is why the skill treats anything above about three quarters of the budget as over it: an estimate of 400 against a budget of 400 is a PR that will be over budget.

## Example: a feature across API and UI

Design: team invites. A table, three endpoints, an email on invite, and a management screen.

| Unit | Anchor | Estimate |
|---|---|---|
| `invites` table, model, hand-written migration | `memberships` model and migration: 140 lines | ~150 |
| Create, list, revoke endpoints with validation and permissions | `memberships` controller: 90 lines per endpoint | ~300 |
| Invite email: template, mailer, queue job | `password_reset` mailer and job: 230 lines | ~250 |
| Management screen: list, invite form, revoke action | `members` screen: 280 lines | ~300 |

Total is about 1,000 lines. Three PRs of 330 would each sit at the edge of the budget with no headroom, so four.

- The schema is a foundation for everything else, so it goes first.
- The API and the email both need the schema but not each other. Both are based on PR 1 and can be reviewed in parallel.
- The screen calls the API, so it stacks on the API PR.

Result: the table shown in `SKILL.md`.

Then the self-contained check, one PR at a time:

- **PR 1** is safe alone because the migration only adds a table and nothing calls the model yet.
- **PR 2** is safe alone because it creates invites whether or not an email goes out, as long as the design says delivery is asynchronous. If the design says "create must fail when the email cannot be queued", the two are no longer independent, and email stacks on the API or merges into it.
- **PR 3** is safe alone because with no invites in the table it has nothing to send.
- **PR 4** is safe alone because every control on the screen calls an endpoint that PR 2 already delivered.

Dependencies come from the design's behaviour, not from which files are touched.

Open order: 1, 2, 3, 4. Merge order: 1, then 2 and 3 in either order, then 4.

## Example: work that fits in one PR

Design: add a `--json` flag to an existing CLI command. One flag definition, one formatter function, a branch in the output code. About 120 review-relevant lines, plus tests.

```markdown
## PR Stack

Single PR: about 120 review-relevant lines, well within the 400-line budget.
```

That is the whole section. Do not manufacture a split to make the skill look useful: a second PR costs the reviewer a context switch and the author a second round trip.

## Hard case: a refactor has to come first

The feature needs an existing function to accept a new parameter, or a module to be split before the new code has somewhere to live.

Put the refactor in its own PR, first, with no behaviour change. A reviewer can check "nothing changed" quickly and confidently when nothing else is in the diff. Mark it *mechanical* if it is purely a rename or a move, in which case the budget does not apply. If the refactor involves real judgment (new abstractions, changed responsibilities), it is not mechanical and the budget does apply.

## Hard case: the change resists splitting

Some changes are atomic: a state machine rewrite, a parser, an algorithm whose pieces are meaningless separately.

First look for seams that are easy to miss:

- **Data before logic.** Types, schemas and constants can land before the code that uses them.
- **New beside old.** Add the new implementation next to the old one, unused. A later, small PR switches callers over, and a third removes the old code. Each step is safe and the risky switch is tiny.
- **Read before write.** A read path can often land before the write path.
- **One case at a time.** If the change handles several input kinds, land the framework with one kind, then the rest.

If none of those apply, keep the PR whole and over budget, and say so in the spec:

```markdown
### PR 2 — Replace billing proration algorithm
- **Over budget (~650 lines):** the proration rules only make sense together, and splitting them
  would leave an intermediate state that bills incorrectly. Reviewer focus below narrows what
  needs the closest reading.
```

Then use **Reviewer focus** to point at the parts that matter most. That does more for the reviewer than an artificial split.

## Hard case: a PR would expose something unfinished

The invite email contains a link to an "accept invite" page. If the email PR merges before the accept page exists, real people receive a link that leads nowhere. Every test passes and the PR is still not self-contained, because a user can reach something half-built.

This is the most common way a stack breaks the self-contained rule, and tests will not catch it. Look for it wherever a PR adds something that points at behaviour: a link, a button, a menu entry, a scheduled job, an outgoing message, a public route.

Three ways to fix it, in order of preference:

- **Reorder.** Put the accept page earlier in the stack than the email, so the link works from the first day it is sent.
- **Combine.** If the two are small, ship them in one PR.
- **Keep it unreachable.** Merge the email code but do not let it run: the sweep is not scheduled, or it sits behind a flag that is off. The PR that completes the flow turns it on. Say exactly what keeps it unreachable in "Safe alone because", so the reviewer can check that claim.

If the missing half is out of scope for the whole spec (accepting invites is "a later project"), the stack as a whole would ship something unfinished. Raise that with the user as a scope question before writing the PR Stack section. It is not something slicing can solve.

## Hard case: schema change with a backfill

Order these so every intermediate state is deployable:

1. Add the new column or table, nullable or with a default. Nothing reads it.
2. Write to both old and new.
3. Backfill existing rows (often a script or job, in its own PR so it can be run and verified separately).
4. Read from the new.
5. Remove the old.

Not every change needs all five as separate PRs. Small steps can share a PR when the result is still deployable at each merge. The point is that no PR in the stack requires a later one to be deployed at the same moment.

## Hard case: one PR needs two independent parents

PR C needs code from both A and B, and A and B do not need each other. A branch has one base, so C cannot be based on both.

Two ways out:

- **Linearise.** Base B on A even though it does not strictly need it, then base C on B. Simple, but B's review is now blocked behind A.
- **Wait.** Keep A and B independent, and do not open C until both have merged, then base C on the base branch. Good when A and B are expected to merge quickly.

Pick linearise by default and say in the spec that B does not truly depend on A, so a reviewer knows it can be re-based if A stalls.

## Checking a split before writing it down

Run each proposed PR through these questions:

- Can I state what it delivers in one sentence without "and"?
- If only this PR and the PRs it is based on merged, and nothing after them ever did, would the product build, pass its tests, and have nothing half-built within a user's reach?
- Does it call, import or link to anything that arrives in a later PR?
- Does it leave every existing caller of the things it changes working?
- Could a reviewer approve it without opening another PR in the stack to understand it?
- Is its base really needed, or could it sit directly on the base branch?
- Does it come after its base in the numbering, so the numbering is also the order to open the PRs in?
- Is it within budget with some headroom? If not, is it mechanical, or is there a stated reason?

A wrong answer on any of the second, third or fourth questions means the slice is cut in the wrong place. Move the boundary before writing the section.
