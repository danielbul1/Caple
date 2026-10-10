---
name: plan-first
description: Understand the goal and write a short verifiable plan before building anything non-trivial - a new feature, a new project, or a change touching several files. Combines Superpowers brainstorming + writing-plans, run autonomously.
---

# Plan First

## A. Understand (brainstorm with yourself)
1. Read the relevant code, README, configs and recent commits. Answer your own questions from them before considering asking the user.
2. Write the goal in one sentence and the success criteria as checks you can run.
3. List 2-3 possible approaches in one line each; choose the simplest that meets the goal (YAGNI) and say why in one line.
4. Record assumptions you made where the request was silent.

*Why:* a design decided in 2 minutes up front saves hours of rework; writing assumptions down makes them reviewable instead of hidden.

## B. Plan
5. Break the work into small steps (each a few minutes of work, independently checkable). For each: what changes, which files, how it's verified.
6. Order by dependency; mark steps that are independent (they can run in parallel).
7. Put the steps in the task list. Keep the whole plan to one screen.

Then start building immediately — don't wait for approval. If reality contradicts the plan, stop, update the plan, then continue; don't improvise around it.
