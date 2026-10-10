# Working rules

- Every coding task follows the `minimal-code` skill.
- Bigger tasks run through the `build` skill, which chains `plan-first` -> `tdd` -> `debug` -> `verify-done` on its own.
- Any bug or failing test: use `debug`. Before saying "done": use `verify-done`.
