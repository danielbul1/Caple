---
name: verify-done
description: Prove work is finished before claiming it. Use right before saying something is done, fixed, passing, or ready to commit/push.
---

# Verify Before Done

Evidence before claims.

1. Name the command that proves the claim (tests, build, lint, running the app and hitting the changed path).
2. Run it fresh, now - not from memory of an earlier run.
3. Read the actual output: exit code, failures, warnings.
4. Report what it shows. If something failed or was skipped, say so plainly.
5. Re-read your own diff once: leftover debug code, unrelated changes, missing files.
