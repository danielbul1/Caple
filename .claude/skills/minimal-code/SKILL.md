---
name: minimal-code
description: Core rules for writing or changing any code - think first, write the least code that works, touch only what the task needs, and prove it works. Use on every coding task, big or small.
---

# Minimal Code

1. **Think first.** State your assumptions. If the request has more than one reading, say so and ask. If a simpler approach exists, propose it.
2. **Least code that works.** No features nobody asked for, no abstractions used once, no config "for later", no error handling for cases that can't happen. Prefer deleting code to adding it.
3. **Surgical changes.** Edit only what the task needs. Don't reformat, rename or refactor nearby code. Match the existing style. Mention unrelated problems instead of fixing them; remove only the dead code your own change created.
4. **Define done, then check it.** Turn the task into a check you can run (a test, a command, a request to the running app) and run it before saying it's finished.

Trivial edits (typos, one-liners) need judgment, not the full ritual.
