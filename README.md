# Santa 2026 — Elf Calculator

Python tools for exact program validation and a first greedy arithmetic solver.
The existing GitHub repository name, `kaggle-santa-2026-elf-calculator`, works well;
no rename is needed. Python 3.11+ is sufficient. There are no external dependencies.

## Quick start (PowerShell, repository root)

```powershell
python -m unittest discover -s tests -v
python -m src.inspect_data data/practice_puzzles.csv
python -m src.solve --workers 4
python -m src.score --puzzles data/practice_puzzles.csv --submission submissions/practice_greedy_v1.csv
```

`src.solve` defaults to the 200 local practice puzzles. It compares a binary
construction baseline with base-4/8/16 greedy candidates, tries ascending,
descending, and seeded random target orders, and validates every result. It
prints total instruction counts, runtime, and the 20 hardest puzzles. Detailed
scores are written to `submissions/solve_report.json`.

## Files you still need

Download the scored puzzle CSV and `sample_submission.csv` from the competition
Data tab after joining and accepting the rules. Put extracted files in `data/`.
Examples below assume the puzzle file is named `scored_puzzles.csv`; substitute
the actual name if different. Practice data is already available at
`data/practice_puzzles.csv`, so development can proceed now.

If the Kaggle CLI is already installed and authenticated, an alternative is:

```powershell
kaggle competitions download -c santa-2026 -p data
```

Extract the downloaded archive. This project does not install the CLI, store
credentials, join the competition, or submit automatically. Keep API credentials
outside the repository. `data/practice_puzzles.csv` is tracked so a fresh clone
includes the practice puzzles. Other data files, generated submissions, and
best-solution caches are ignored.

## Confirm the official sample first

Read [the rule notes](docs/competition.md), confirm initialization/target coverage
against the Data page, then run:

```powershell
python -m src.inspect_data data/scored_puzzles.csv
python -m src.score --puzzles data/scored_puzzles.csv --submission data/sample_submission.csv --competition --report submissions/sample_report.json
python -m unittest discover -s tests -v
```

The official sample integration test skips until both files exist. Current
results are local practice results, not an official sample or leaderboard score.

## Generate and validate a scored submission

```powershell
python -m src.solve --puzzles data/scored_puzzles.csv --output submissions/greedy_v1.csv --report submissions/scored_report.json --workers 4 --restarts 2 --competition
python -m src.score --puzzles data/scored_puzzles.csv --submission submissions/greedy_v1.csv --competition
```

`--competition` requires exactly all 1,000 scored IDs. Upload only a successfully
validated scored CSV. Increase `--restarts` for more seeded target orders; use
`--bases 4 8` to reduce search time. `--seed` defaults to 2026. On constrained
machines use `--workers 1`. Solvers use exact integer arithmetic throughout.

Best programs are kept per puzzle in `cache/best`, fingerprinted by the entire
puzzle definition. Re-running never replaces a valid cached program with a
longer one. Corrupt cache entries fail explicitly. Use one solve process per
cache directory; its workers compute while the parent alone updates the cache.
Merge all cached solutions without solving again:

```powershell
python -m src.merge --puzzles data/scored_puzzles.csv --output submissions/best.csv --competition
```

## How the first solver works

The solver keeps constants and useful results in registers. If one operation
between stored values can produce a remaining target, it takes it immediately.
Otherwise it constructs a target in a chosen base, reusing an existing prefix
when available. It retains results and evicts the least recently used unprotected
register. Partial base-expansion values never exceed their target. A deterministic
binary construction is always tried as a fallback and comparison. Every candidate
is independently replayed before selection, caching, and CSV export.

This bounded greedy strategy is a starting point. It does not perform arbitrary
intermediate exploration, prime factorization, beam search, or instruction
rewriting. These are useful next steps after measuring the scored baseline.

## Project map

```text
kaggle-santa-2026-elf-calculator/
├── AGENTS.md
├── README.md
├── .gitignore
├── docs/                  # Rules, data notes, and reusable Codex prompt
├── data/                  # Other local Kaggle files are ignored
│   └── practice_puzzles.csv # Tracked practice input
├── src/                   # Validator, solver, scoring, and cache tools
├── tests/
├── submissions/           # Generated CSVs and reports (ignored)
└── cache/                 # Best-known programs (ignored)
```

- `AGENTS.md`: ongoing coding rules for this repository.
- `docs/competition.md`: supplied competition rules and open assumptions.
- `docs/data_notes.md`: local practice schema and validation results.
- `docs/codex_prompt.txt`: comprehensive prompt for a future coding session.
- `src/io.py`, `src/validator.py`, `src/score.py`: parsing, replay, and scoring.
- `src/greedy.py`, `src/solve.py`: greedy construction and parallel runs.
- `src/cache.py`, `src/merge.py`: validated best-known solutions and export.
- `tests/`: unit, randomized solver, CSV, cache, and optional official sample checks.
