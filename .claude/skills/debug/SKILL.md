---
name: debug
description: Systematic debugging - find the root cause before fixing. Use for any bug, failing test, crash, or unexpected behavior.
---

# Debug

No fix before you know the root cause.

1. **Reproduce.** Get a reliable, minimal repro. Read the full error and stack trace.
2. **Narrow.** Check what changed (git diff/log). Trace the bad value back to where it first goes wrong. Add logging or a quick script instead of guessing.
3. **Hypothesis.** One specific cause at a time; test it with the smallest experiment. If it's wrong, revert the experiment and form a new one.
4. **Fix the cause, not the symptom.** Add a test that fails without the fix, then apply one minimal fix.
5. **Verify** the repro is gone and nothing else broke.

If three fixes in a row fail, stop: the mental model is wrong. Step back and question the design or ask.
