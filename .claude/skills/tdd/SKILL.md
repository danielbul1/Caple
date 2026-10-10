---
name: tdd
description: Test-driven development - red, green, refactor. Use when adding behavior or fixing a bug in code that has, or can easily get, tests.
---

# TDD

1. **Red.** Write one small test for the next behavior (or one that reproduces the bug). Run it; watch it fail for the expected reason.
   *Why:* a test you never saw fail might not test anything.
2. **Green.** Write the minimum code that makes it pass. Nothing extra.
   *Why:* code beyond what a test demands is untested code.
3. **Refactor.** Clean up while everything is green; run the full suite.
4. Repeat for the next behavior.

Rules:
- Test behavior through the public interface, not implementation details.
- Mock only real boundaries (network, clock, disk, paid APIs).
- Never weaken, skip or delete a test to get green.
- No test setup in the project? Add the smallest one the stack supports (e.g. `pytest` for Python) rather than skipping tests.
