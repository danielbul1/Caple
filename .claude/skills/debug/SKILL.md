---
name: debug
description: Systematic debugging - find the root cause before fixing. Use for any bug, failing test, crash, error, or unexpected behavior.
---

# Debug

**No fix before the root cause is known.** *Why:* guessed fixes hide the bug, add new ones, and waste more time than investigating.

1. **Reproduce.** Get a reliable, minimal repro. Read the entire error and stack trace — the answer is often in it.
2. **Narrow.** What changed (git diff / log)? Trace the bad value backward to where it first goes wrong. Add logging or a tiny script instead of guessing. Compare with a similar piece of code that works.
3. **Hypothesis.** One specific cause at a time; test it with the smallest experiment. Wrong? Revert the experiment, form the next one.
4. **Fix the cause.** Write a test that fails because of the bug, then apply one minimal fix and watch it pass.
5. **Verify** the original repro is gone and the full suite still passes.

**Three failed fixes = stop.** The mental model is wrong. Re-read the code from scratch, question the design, and only then try again (or report it as blocked).
