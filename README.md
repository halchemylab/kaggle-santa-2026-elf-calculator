# Santa 2026 — Elf Calculator

Python tools for exact program validation and a first greedy arithmetic solver.
The existing GitHub repository name, `kaggle-santa-2026-elf-calculator`, works well;
no rename is needed. Python 3.11+ is sufficient. There are no external dependencies.

Project closed after the first successful Kaggle submission on November 27, 2026.
The independently developed solver scored **392,980**, exactly matching local
validation across all 1,000 puzzles. No public solution programs were imported.
The final method was `factor_prefix`, with 13 candidates and seed 2026. Source,
tests, and experiment notes are preserved; downloaded data and generated files
remain local and ignored by Git.

Returning to the project? Start with [next-session notes](docs/next_session.md).
The latest [program diagnosis](docs/program_diagnosis.txt) records search-budget
results, the prefix-retention probe, and commands to reproduce both.

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

The selected factor/offset method is also available for validated exports:

```powershell
python -m src.solve --method factor_offset --candidates 13 --seed 2026 --workers 4 --output submissions/practice_factor_offset_v1.csv --report submissions/practice_factor_offset_report.json
python -m src.score --puzzles data/practice_puzzles.csv --submission submissions/practice_factor_offset_v1.csv
```

Explicit `--method` choices use the same solver interface, per-puzzle seed, and
candidate schedule as benchmarks. The default candidate cap is 13. `--restarts`
and `--bases` apply only to commands without `--method`; existing commands keep
their original greedy behavior. The default output is
`submissions/practice_<method>_v1.csv`; `--competition` requires an explicit output
path. Exports may include shorter validated cached programs, so use `src.benchmark`
for fresh comparisons. Reports record the selected method, interface, and budget.

## Compare algorithms and review runs

```powershell
python -m src.benchmark --workers 4 --label "First comparison"
```

This compares binary construction, larger-base construction, greedy, factor/offset
construction, experimental prefix retention, and a tiny-puzzle beam search on a fixed 160-puzzle development set,
with three seeds. Every result is
measured fresh and independently validated. It saves a new run under `runs/` and
automatically rebuilds **`runs/dashboard.html`**. Open that file in your browser.

The dashboard includes run and method selectors, instruction counts, runtime,
per-puzzle wins/ties/losses, search and sorting, seed consistency, validated program
downloads, and run history. You can compare two runs with matching puzzle definitions.
Incompatible puzzle sets are blocked; unequal configured budgets are flagged.

For a quicker experiment:

```powershell
python -m src.benchmark --methods binary base_expansion greedy --seeds 2026 --candidates 7 --workers 4 --label "Quick test"
```

The frozen split is in `benchmarks/practice_split.json`: 160 development puzzles and
40 holdout puzzles. `--split holdout` evaluates the holdout explicitly; use it after
choosing settings on development puzzles. The earlier setup run used all 200 puzzles,
so this holdout is a future tuning boundary rather than a completely unseen dataset.
See [benchmark details](docs/benchmarking.md) for budgets, saved artifacts, adding
solvers, and the first comparison results. Benchmark runs do not read or update the
best-known cache unless you explicitly pass `--update-cache cache/best`.

Rebuild the dashboard from saved runs at any time:

```powershell
python -m src.dashboard
```

Run records and generated dashboards are ignored by Git. Source code and the frozen
split are tracked; on another computer, run the command again to create local results.

## Official competition files

Download the scored puzzle CSV and `sample_submission.csv` from the competition
Data tab after joining and accepting the rules. Put extracted files in `data/`.
The official filenames are `puzzles.csv` and `sample_submission.csv`. Both are
available locally as of November 27 and remain ignored by Git. Fresh clones need
their own downloads. Practice data is tracked at `data/practice_puzzles.csv`.

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

The [official Data rules](docs/competition.md) confirm that starting values occupy
consecutive registers and count toward target coverage. To validate the sample:

```powershell
python -m src.inspect_data data/puzzles.csv
python -m src.score --puzzles data/puzzles.csv --submission data/sample_submission.csv --competition --report submissions/official_sample_report.json
python -m unittest discover -s tests -v
```

The official sample validates locally: 1,000 programs, 1,490,379 instructions,
maximum 2,873 per puzzle. The integration test skips only when the files are absent.
The first solver submission was subsequently accepted by Kaggle at 392,980,
matching local validation. The sample total above is its local reference score.

## Generate and validate a scored submission

```powershell
python -m src.solve --puzzles data/puzzles.csv --method factor_prefix --candidates 13 --seed 2026 --workers 4 --cache cache/scored_factor_prefix_13 --output submissions/scored_first.csv --report submissions/scored_first_report.json --competition
python -m src.score --puzzles data/puzzles.csv --submission submissions/scored_first.csv --competition --report submissions/scored_first_validation.json
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
python -m src.merge --puzzles data/puzzles.csv --output submissions/best.csv --competition
```

## How the first solver works

The solver keeps constants and useful results in registers. If one operation
between stored values can produce a remaining target, it takes it immediately.
Otherwise it constructs a target in a chosen base, reusing an existing prefix
when available. It retains results and evicts the least recently used unprotected
register. Partial base-expansion values never exceed their target. A deterministic
binary construction is always tried as a fallback and comparison. Every candidate
is independently replayed before selection, caching, and CSV export.

The `factor_offset` method also tries retained-value products with
small signed offsets and sums/differences with retained values. It constructs one
quotient or difference by base expansion and uses the plan only when its estimated
instruction count is shorter than plain expansion. It uses the same candidate
schedule and binary fallback as greedy. Select it with
`src.solve --method factor_offset --candidates 13`. A separate experimental beam
method handles tiny puzzles only.

The experimental `factor_prefix` method uses the same factor/offset planning and
candidate schedule, but allocates a register for each base digit so earlier
prefixes can survive for reuse. It is compared independently against
`factor_offset`; neither method reads cached solutions in benchmarks.

```powershell
python -m src.benchmark --methods factor_offset factor_prefix --seeds 2026 2027 2028 --candidates 49 --workers 4 --split train --label "Prefix retention full development comparison - 49 candidates"
```

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
├── benchmarks/            # Frozen development/holdout IDs
├── runs/                  # Benchmark records and local dashboard (ignored)
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
- `src/solvers.py`, `src/benchmark.py`: common solver interface and fresh comparisons.
- `src/dashboard.py`, `src/dashboard.html`: offline run comparison dashboard.
- `tests/`: unit, randomized solver, CSV, cache, and optional official sample checks.
