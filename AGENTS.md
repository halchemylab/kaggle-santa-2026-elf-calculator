# Santa 2026 — Elf Calculator

Read README.md and docs/competition.md before changing solver behavior.

- Use Python 3.11+ and the standard library. No additional dependencies without approval.
- Correctness comes first: validate every generated or cached program before export.
- Use exact Python integers, never floats, for calculator arithmetic.
- Registers contain positive integers bounded by each puzzle's value_limit.
- Read both operands before overwriting a destination; division must be exact.
- Limits: 48 registers, 4,096 instructions, 131,072 UTF-8 bytes per program cell.
- Keep scored and practice results separate. Only a complete set of scored_0001 through
  scored_1000 may be labeled a competition submission.
- Initial target coverage is unconfirmed: default to explicitly producing initial targets.
- Data belongs in data/; generated CSVs in submissions/; solutions in cache/.
  Track data/practice_puzzles.csv so fresh clones include practice input.
  Other data files, generated submissions, and caches are ignored.
- Cache entries must match the puzzle fingerprint and validate before reuse. Replace
  an existing valid solution only with a shorter valid solution.
- Run `python -m unittest discover -s tests -v` after behavioral changes.
- Run commands as modules, e.g. `python -m src.solve`, from the repository root.
