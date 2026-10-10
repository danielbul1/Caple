---
name: verify-done
description: Prove work is finished before claiming it. Use right before saying something is done, fixed, passing, or ready to commit/push.
---

# Verify Before Done

**Evidence before claims.** *Why:* "it should work" is the most common lie in software.

1. Name the commands that prove the claim: full test suite, build/lint/typecheck if the repo has them, and run the app and exercise the changed path if it's runnable.
2. Run them fresh, now — not from memory of an earlier run.
3. Read the actual output: exit codes, failures, warnings.
4. Re-read the final diff: leftover debug code, unrelated changes, missing files, secrets.
5. Report exactly what the output shows. Anything failed, skipped or unverifiable gets said plainly.
