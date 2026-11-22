# Comparing solver experiments

The benchmark measures fresh solutions on identical puzzle definitions. The primary
score is total instructions with every puzzle valid. Runtime, seed sensitivity,
and per-puzzle wins/losses help decide which experiments deserve more computation.
No reported score is a proof of optimality or a Kaggle leaderboard score.

## First commands

```powershell
python -m src.benchmark --workers 4 --label "Development baseline"
python -m src.dashboard
```

Open `runs/dashboard.html` by double-clicking it. It works offline and uses no
external scripts or fonts. Each benchmark automatically rebuilds it. Reopen or
refresh after a run; it contains a snapshot of the saved reports, not live polling.
Keep the HTML in `runs/` so its default relative program links work. Custom output
paths are supported and program links are calculated relative to the chosen file.

The dashboard compares any selected method/seed against another selected method/seed,
within one run or across runs. It blocks comparison when puzzle IDs or fingerprints
differ. It shows per-seed totals, mean/range/standard deviation across complete seeds,
validity, task runtime, per-puzzle savings, errors, and the combined best-per-puzzle
portfolio. Search or filter for candidate wins, losses, ties, or invalid results.
Positive steps saved always means the candidate uses fewer instructions.

## Controlled methods

| Method | Behavior |
| --- | --- |
| binary | One deterministic base-2 construction; reused stored prefixes are allowed |
| base_expansion | Binary fallback plus base-4/8/16 constructions; immediate-target scan disabled |
| greedy | Identical candidate schedule to base_expansion, with immediate-target scan enabled |
| factor_offset | Greedy plus retained-value factors with small signed offsets, and nearby retained-value sums/differences |
| beam | Binary fallback plus bounded primitive-instruction beam search on tiny puzzles |

All methods use `solve(puzzle, method, seed=..., budget=SearchBudget(...))` in
`src/solvers.py`. Results contain the program plus candidate counts, expanded-state
counts, budget status, and notes. The benchmark independently replays the returned
program. A solver error or invalid final program is recorded as a failed result:
it contributes no score, produces no full CSV for that method/seed, and cannot enter
the best-program cache. A method/seed total is null unless the entire selected set
validated. The portfolio total is also null unless it covers every selected puzzle.

Base-expansion and greedy always compare against their own binary fallback; they
cannot return a longer valid program. Candidate order cycles bases 4/8/16, first
ascending targets, then descending, then seeded random orders. The default cap of
13 includes the binary fallback and 12 alternative constructions. Seeds influence
random orders; binary and the current beam search are deterministic. Repeated
deterministic seeds provide timing repetitions, not different search trajectories.

`factor_offset` uses that same candidate schedule and binary fallback. Before
expanding a target, it estimates plans of the form `retained * quotient +/- offset`
and `retained +/- difference`. Offsets are stored constants 1 through the candidate
base (or zero); one quotient/difference is constructed with ordinary prefix reuse.
Only plans strictly cheaper than direct expansion are emitted. Required retained
operands are protected against eviction. Every intermediate must respect the value
limit, including products before a subtraction. This is bounded local planning,
not prime factorization or recursive search. Changing the path can change later
register reuse, so individual puzzles can regress against greedy despite cheaper
local plans. Equal candidate caps also do not imply equal runtime.

Beam search currently applies only when value_limit <= 512, distinct targets <= 6,
and initial values <= 8. It searches individual legal instructions, preserves
historical coverage, deduplicates equivalent states, and keeps the best-ranked
states at each depth. It keeps intermediate values in free registers and does not
search register eviction. Defaults: width 24, depth 10, and 250 expanded states.
Large puzzles use the binary fallback and record a skip note. Therefore its
whole-dataset total measures this limited beam/fallback combination; it does not
establish whether a broader beam method would be competitive.

## Search budgets and timing

```powershell
python -m src.benchmark --methods binary base_expansion greedy --seeds 2026 2027 2028 --candidates 13 --workers 4
python -m src.benchmark --methods base_expansion greedy --seeds 2026 --candidates 1000 --seconds 0.1 --workers 1 --label "Soft time budget"
```

`--seconds` is a soft per-puzzle limit. Every method completes the binary fallback
first. Time is checked between construction candidates or beam state expansions;
one work unit and output validation may finish after the deadline. This is not a
hard process timeout. A fixed seed and candidate count reproduce programs when
there is no time cutoff. Time cutoffs may change which candidates finish.

Compare search quality under the same settings, seeds, and selected puzzles. For
time-budget experiments use a high candidate cap and the same `--seconds` and
worker count. The candidate cap and beam expansion cap count different work units,
so equal caps alone do not imply equal computation across algorithm families.
Recorded task seconds include fallback, solver work, and independent validation.
They exclude queue wait. Summed task seconds overlap under multiprocessing; run wall
time also includes collection and artifact writing. Runtime is machine-dependent
and parallel contention can affect it. Do not treat small timing differences as
established speedups.

## Frozen split

`benchmarks/practice_split.json` fixes 160 train/development and 40 holdout IDs
using a stable hash ordering. It also identifies the entire dataset by fingerprints.
Reordered input rows are accepted; changed puzzle definitions require a new split
manifest path, e.g. `--split-file benchmarks/new_dataset_split.json`.

Default: `--split train`. Use `--split holdout` explicitly after deciding settings;
`--split all` intentionally evaluates both partitions. The earlier repository setup
used all 200 puzzles, so the split is not a claim that these puzzles have never been
observed. Keep it stable for future tuning rather than repeatedly adjusting settings
to holdout results. The benchmark never reads the best-program cache. Cache updates
are opt-in through `--update-cache DIRECTORY` and always validate before writing.

## Saved artifacts

Each immutable `runs/<UTC timestamp>-<unique suffix>/` contains:

- `report.json`: puzzle fingerprints, configuration, seed results, comparison to
  binary, seed statistics, portfolio, timing, and errors.
- `source/`: the actual Python/HTML implementation used when the run started.
  SHA-256 hashes accompany the snapshot. This preserves uncommitted implementations.
- `programs/<method>_seed_<seed>.csv`: complete, validated program sets. These may
  be development or holdout subsets; they are not automatically competition submissions.

CLI metadata records the dataset, split, Git revision and dirty status, Python and
platform versions, workers, timing policy, and whether best-cache updates were enabled.
Run IDs are unique; existing run directories are never overwritten. Run history
stays local in ignored `runs/`. Copy that directory separately to transfer past runs;
cloning the code alone lets another machine generate new runs.

## First development-set comparison

Run `20261122T024949Z-ee4bf536`, label `Initial four-method comparison`:
160 development puzzles, four workers, three seeds (2026–2028), 13 construction
candidates, and the default beam bounds. All 1,920 final programs validated.
The 40 holdout puzzles were not evaluated by this benchmark. Wall time: about 57.6 s.

| Method | Total instructions per seed |
| --- | ---: |
| binary | 226,626 |
| base_expansion | 74,136 |
| greedy | 74,030 |
| beam with binary fallback | 226,571 |

Each method produced the same total for all three tested seeds. The best-per-puzzle
portfolio across all methods/seeds was 74,008 instructions. Keep that separate from
any individual method score. A prior control run used a one-candidate construction
cap; beam still had its separately configured expansion budget.

The controlled comparison shows larger-base construction accounts for most of the
improvement over binary here. Enabling immediate-target greediness saves another
106 net instructions under this candidate schedule. Beam improves some tiny puzzles
but falls back to binary for large ones. Three matching seed totals do not prove
randomized target ordering will never help.

## Development experiment results

### Factor/offset development experiment (November 22, 2026)

Run `20261122T210642Z-9ed33410`, label `Factor and retained-value offset experiment`:
160 development puzzles, seeds 2026/2027/2028, 13 candidates, four workers, no time
cutoff, no cache access. Puzzle definitions matched the recreated baseline run
`20261122T210130Z-5034510c`. All 1,920 programs validated, and all 12 exported CSVs
were independently replayed successfully. The holdout was not evaluated.

| Method | Seed 2026 | Seed 2027 | Seed 2028 | Mean summed task seconds per seed |
| --- | ---: | ---: | ---: | ---: |
| binary | 226,626 | 226,626 | 226,626 | 1.81 |
| base_expansion | 74,136 | 74,136 | 74,136 | 11.31 |
| greedy | 74,030 | 74,030 | 74,030 | 55.20 |
| factor_offset | 64,294 | 64,290 | 64,309 | 122.22 |

Factor/offset saved 9,721–9,740 instructions (13.13–13.16%) versus greedy. Each
seed improved 144 puzzles, tied 16, and regressed on none. The largest saving was
146 instructions on `practice_0153`. This is an observed result, not a guarantee
against future regressions. The method used about 2.2 times greedy's mean summed
task time in this run; equal candidate counts do not equalize work. Total run wall
time was 148.3 seconds. The combined best-per-puzzle portfolio across all methods
and seeds was 64,238 instructions, separate from any individual method/seed score.

The new method is available through `src.solvers` and `src.benchmark`; the
submission-solving CLI still uses the original greedy implementation.

```powershell
python -m src.benchmark --methods binary base_expansion greedy factor_offset --seeds 2026 2027 2028 --candidates 13 --workers 4 --split train --label "Factor and retained-value offset experiment"
```

## Adding an experiment

Add a method name and dispatch in `src/solvers.py`, preserving the same interface.
Test it on small puzzles, malformed/invalid outputs, budget exhaustion, and
reproducibility. Keep the simulator independent. Run the baseline and candidate on
the same development split and save a labeled report before selecting settings.
Only then evaluate the holdout. Future learned policies can rank beam candidates
or estimate remaining cost while exact arithmetic and replay enforce legality.

Checks:

```powershell
python -m unittest discover -s tests -v
node tests/check_dashboard.cjs runs/dashboard.html
```

Node is optional and used only for the dashboard script smoke check, which expects
at least two saved runs. It tests interactions with a minimal DOM fixture; it is
not a browser layout or screenshot test. No browser was connected during initial
implementation, so visual rendering still needs a local browser check.
