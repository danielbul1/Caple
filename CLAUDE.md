# Working rules

Skills in `.claude/skills/` combine Superpowers' workflow with Karpathy's guidelines. Use them without being asked:

- Any request to build, add, change or fix something bigger than a one-liner → run the `build` skill end to end, autonomously (it chains `plan-first` → `tdd` → `debug` → `review` → `verify-done` → commit & push).
- Every line of code follows `minimal-code`.
- Any bug or failing test → `debug`. Before saying "done" → `verify-done`.
- Don't stop to ask unless truly blocked (missing secret/access, a product decision with no sensible default, or an irreversible outward action). Otherwise decide, record the assumption, and continue.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for danielbul1/Caple (via `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
