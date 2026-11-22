# Local practice data and first run

Inspected November 21, 2026. Only `data/practice_puzzles.csv` is currently available.
Neither scored puzzle data nor the official sample submission has been downloaded.

## Schema

| Column | Parsed representation | Use |
| --- | --- | --- |
| id | string | Unique puzzle identity |
| starting_values | JSON array of integers | Initial register values |
| targets | JSON array of integers | Historical target coverage |
| value_limit | integer | Inclusive bound for every register value |
| registers | integer | Always 48 in the local file |
| family | string | Practice diagnostic metadata |
| design_tier | string | Practice diagnostic metadata |
| lower_bound | integer text | Practice reference, not an achieved score |

The loader reads only the five mandatory columns. Values are parsed with JSON
and integer conversion, never `eval` or floating-point conversion. IDs are unique.

| Measure | Observed range / count |
| --- | --- |
| Puzzles | 200 |
| Targets per puzzle | 1–32 |
| Target values | 1–998,263,746,689,377,336 |
| Starting values per puzzle | 1–8 |
| Starting values | 1–1,973 |
| value_limit | 7–998,748,313,126,407,437 |
| Tiers | 170 hard, 14 medium, 16 easy |

The first row has four starting values, 30 targets, and the `multiplicative`
family; the next has three starting values, 29 targets, and the `mixed` family.
Raw target lists remain in the source CSV rather than being duplicated here.

## First reproducible solver run

Command: `python -m src.solve --workers 4`.
Seed 2026, bases 4/8/16, ascending and descending orders plus two random restarts
per base. The cache was initially empty. Runtime: approximately 14.4 seconds on
the setup machine, including candidate replay, cache writes, and CSV export.

| Strategy | Total instructions over 200 practice puzzles |
| --- | ---: |
| Local binary construction | 289,566 |
| Best first greedy candidates | 94,523 |

This is a 67.36% reduction from the local binary baseline. It is not a comparison
against Kaggle's sample submission or a leaderboard result. The greedy total
includes constant setup and every emitted instruction.

| Practice family | Puzzles | Total steps | Mean steps |
| --- | ---: | ---: | ---: |
| multiplicative | 40 | 12,267 | 306.7 |
| mixed | 48 | 27,456 | 572.0 |
| shared | 51 | 23,882 | 468.3 |
| independent | 45 | 30,840 | 685.3 |
| tiny | 16 | 78 | 4.9 |

Hardest programs: `practice_0055` (888), `practice_0179` (887),
`practice_0018` (886), `practice_0054` (886), and `practice_0135` (884).
The full worst-20 list and per-puzzle scores are in the generated JSON report.

Outputs (ignored by Git):

- `submissions/practice_greedy_v1.csv`: validated practice programs.
- `submissions/solve_report.json`: baseline/best counts, configuration, and runtime.
- `submissions/practice_validation.json`: independent CSV replay, 200 valid, zero errors.
- `submissions/practice_best.csv`: cache merge, also 94,523 steps and fully validated.
- `cache/best/`: fingerprinted best-known programs.

## Validation and remaining work

Unit tests cover exact replay, aliasing, historical coverage, conservative initial
coverage, illegal arithmetic and register indices, malformed programs, program
limits, CSV identity/completeness, cache retention, randomized puzzles, large
integers, and register eviction. The optional official sample test skips until
its input files are provided. The complete practice CSV was independently scored
after export and the cache merge was replayed before export.

The official Data page could not be retrieved during setup. Initialization into
consecutive registers and the treatment of initial target values still need
confirmation; see docs/competition.md. Explicitly reproducing initial targets
keeps generated programs conservative. No official sample score is available.

Next useful experiments: factor-aware chains for multiplicative/mixed puzzles,
offset construction from retained targets for shared puzzles, and prefix sharing
or beam search for expensive independent puzzles. Measure improvements against
the existing validated per-puzzle cache. Safe instruction removal should use
dependency/liveness analysis followed by full replay, since register reuse makes
naive deletion unsafe.
