---
name: minimal-code
description: Karpathy-style rules for writing or changing any code - think first, least code that works, surgical changes, goal-driven verification. Use on every coding task, big or small.
---

# Minimal Code

1. **Think before coding.** State assumptions. If the request has two readings, pick the one the code supports and say which. If a simpler approach exists, take it.
   *Why:* most wasted work comes from solving the wrong problem confidently.
2. **Simplicity first.** Write the least code that solves the problem. No unrequested features, no one-use abstractions, no config "for later", no handling for cases that can't happen. Deleting beats adding.
   *Why:* every line is something to read, test and maintain; speculative code is usually wrong when "later" arrives.
3. **Surgical changes.** Touch only what the task needs. Don't reformat, rename or refactor nearby code; match the existing style. Mention unrelated issues instead of fixing them. Remove only the dead code your own change created.
   *Why:* a small diff is easy to review, easy to revert, and can't break what it didn't touch.
4. **Goal-driven execution.** Turn the task into a check you can run (a failing test, a command, a request to the app). Work until it passes, then stop.
   *Why:* "done" must be observable, not a feeling.

Trivial edits (typos, one-liners) need judgment, not the full ritual.
