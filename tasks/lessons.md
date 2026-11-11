
## 2026-11-11: CI went red six pushes in a row
- Pattern: I ran pytest and ruff before pushing, but not `python tools/mutate.py`, which CI also runs. Editing a line a mutation targets makes it stale and CI fails.
- Rule: before any push that touches tempo/, run `python tools/mutate.py` (about 10 min) or at least the module's section; after pushing, check `gh run list --limit 1`. Never push again on a red CI without fixing it first.
