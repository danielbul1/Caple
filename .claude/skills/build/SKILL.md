---
name: build
description: Autonomous end-to-end pipeline combining Superpowers' workflow with Karpathy's guidelines - understand, plan, build test-first, debug, self-review, verify, ship. Use for any request to build, add, change or fix something that is more than a one-line edit, even if the user doesn't name this skill.
argument-hint: <what to build or fix>
---

# Build — autonomous pipeline

Task: $ARGUMENTS

The user starts this once and expects a finished, verified, pushed result. Run every phase yourself, in order, without waiting for approval. `minimal-code` applies to every line you write.

**Why this order:** each phase catches a different failure early, when it is cheap — wrong goal (1), wrong design (2), wrong code (3-4), blind spots (5), false "done" (6).

## Phases

1. **Understand** → `plan-first` part A. Read the code, infer the goal, write down assumptions.
2. **Plan** → `plan-first` part B. Small steps, each with its own check. Track them in the task list so progress survives a long session.
3. **Build** → for each step, `tdd` (or a concrete runnable check where tests don't fit). One step at a time; mark it done only when its check passes.
   - 3+ steps that don't touch the same files? Hand each to a fresh subagent with the step, its files and its check, then review what each returns before accepting it. Fresh context = no drift, parallel = faster.
4. **Fix** → anything fails or surprises you: `debug`. Root cause first, then back to the step.
5. **Review** → `review`: a fresh-eyes subagent reviews the full diff against the goal; you verify and fix the real findings.
6. **Verify** → `verify-done` on the whole change.
7. **Ship** → commit with a message that says what and why, push to the current branch.
8. **Report** in ≤8 lines: what was built, the evidence it works (real output), the assumptions you made, anything skipped or open.

## Autonomy rules

- **Decide, don't ask.** On an open question, pick the simplest, most reversible option that fits the codebase, note it as an assumption, and continue. The user reviews assumptions in the report.
- **Ask only when truly blocked:** a secret or access you don't have, a product decision with no sensible default, or an irreversible/outward action (deleting data, deploying to prod, paying, emailing people).
- **Stay in scope.** Unrelated problems you notice go in the report, not in the diff.
- **Never fake progress.** No skipped/weakened tests, no "should work". If something can't be verified, say so.
