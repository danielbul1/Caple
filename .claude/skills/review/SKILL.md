---
name: review
description: Self code review with fresh eyes before shipping - a subagent reviews the diff, then each finding is verified before acting on it. Use after implementation, before the final verify and commit.
---

# Review

*Why:* the author's context hides the author's mistakes. A reviewer that only sees the goal and the diff catches what you can't.

1. **Request.** Spawn a fresh subagent. Give it only: the goal and success criteria, the assumptions, and the diff (`git diff` against the starting point). Ask it to report, ranked: bugs, requirements missed, unnecessary code or scope creep (per `minimal-code`), missing tests. Each finding with file, line and a concrete failing scenario.
2. **Receive critically.** Treat each finding as a claim, not an order. Verify it against the code — reproduce it or trace a real path.
   - Real and in scope → fix it (via `tdd`/`debug`).
   - Not real, or not worth its code → skip it, note why in one line.
   - Out of scope → put it in the final report.
3. Fixed anything non-trivial? Re-run the review once on the new diff.

Don't argue with yourself forever: one review round, plus one more only if the first round changed real logic.
