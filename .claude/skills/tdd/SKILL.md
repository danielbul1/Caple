---
name: tdd
description: Test-driven development - red, green, refactor. Use when adding behavior or fixing a bug in code that has (or should have) tests.
---

# TDD

1. **Red.** Write one small test for the next behavior (or one that reproduces the bug). Run it and watch it fail for the right reason. A test you never saw fail proves nothing.
2. **Green.** Write the minimum code that makes it pass. Nothing extra.
3. **Refactor.** Clean up with all tests green. Run the full suite.
4. Repeat for the next behavior.

Rules: test behavior, not implementation details. Mock only at real boundaries (network, clock, disk). Never weaken or delete a test to get green.
