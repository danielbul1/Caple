---
name: build
description: One-shot autonomous pipeline that chains the other skills - plan, build test-first, debug, verify, commit. Use when the user says "build X", "/build X", or hands over a feature/fix to finish end to end.
argument-hint: <what to build or fix>
---

# Build (autonomous)

Task: $ARGUMENTS

Run the whole pipeline yourself, start to finish, without stopping for approval. Apply `minimal-code` throughout.

1. **Plan** - follow `plan-first`. Ask the user only if a decision is truly theirs and can't be inferred from the code or a sensible default; otherwise write the plan down in a few lines and keep going.
2. **Build each step** - follow `tdd` when the code has (or can easily get) tests; otherwise define a concrete check for the step (a command, a request to the running app).
3. **On any failure** - switch to `debug`. Find the root cause, fix it, return to the step.
4. **Finish** - follow `verify-done` on the whole change: full test suite, run the app if it has one, re-read the diff.
5. **Ship** - commit with a clear message and push to the current branch.
6. **Report** in a few lines: what was built, how it was verified (with real output), anything skipped or still open.

Stop early only when blocked on something only the user can provide (a secret, a product decision, access).
