# Comparing solver experiments

The benchmark measures fresh solutions on identical puzzle definitions. The primary
score is total instructions with every puzzle valid. Runtime, seed sensitivity,
and per-puzzle wins/losses help decide which experiments deserve more computation.
No reported score is a proof of optimality or a Kaggle leaderboard score.

On November 27 the official Data rules confirmed that initially present targets
count as covered. New runs record `metadata.initial_targets_count: true`.
Historical reports without that field used explicit initial-target production.
The dashboard blocks cross-policy comparisons even with matching puzzle
fingerprints. Recreate fresh baselines under the confirmed policy before tuning.

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
| factor_prefix | Factor/offset planning with a new destination for each base digit, retaining earlier prefixes under LRU |
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

`factor_prefix` isolates prefix retention: it allocates a destination at each
base digit, rather than overwriting all prefixes in one accumulator. This changes
which values survive and therefore can change later plans. Its binary fallback,
target order schedule, bases, and candidate cap match `factor_offset`. It does
not also run factor/offset candidates as a fallback; measuring both separately
lets us observe regressions without doubling the experimental method's budget.
The default `src.solve` behavior and `factor_offset` implementation are unchanged.

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

The method is available through `src.solvers`, `src.benchmark`, and
`src.solve --method factor_offset --candidates 13`.

```powershell
python -m src.benchmark --methods binary base_expansion greedy factor_offset --seeds 2026 2027 2028 --candidates 13 --workers 4 --split train --label "Factor and retained-value offset experiment"
```

### Selected-settings holdout evaluation (November 24, 2026 local time)

The post-pull development rerun `20261125T041020Z-0cc87e75` exactly reproduced
the instruction totals above, with matching puzzle fingerprints. Settings were
then frozen before evaluating the 40-puzzle holdout: 13 candidates, seeds
2026/2027/2028, four workers, no time cutoff, and no cache access.

Holdout run `20261125T041327Z-2f0ea9b9`:

| Method | Seed 2026 | Seed 2027 | Seed 2028 |
| --- | ---: | ---: | ---: |
| greedy | 20,493 | 20,493 | 20,493 |
| factor_offset | 17,700 | 17,673 | 17,675 |

Factor/offset improved all 40 puzzles in every seed, with no ties or regressions.
Savings were 2,793–2,820 instructions (13.63–13.76%). All 240 programs validated;
all six exported CSVs were independently replayed successfully. Wall time was
30.0 seconds; mean summed task time was about 2.5 times greedy's on this machine.
The combined portfolio was 17,670 instructions; it is separate from each individual
method/seed score. These remain practice results. The holdout has now been evaluated;
do not tune settings against it.

The selected method is now exposed in `src.solve`. Existing invocations retain
their historical greedy schedule; explicit `--method` uses benchmark seeds and
budgets. Cache and export validation are unchanged.

```powershell
python -m src.benchmark --methods greedy factor_offset --seeds 2026 2027 2028 --candidates 13 --workers 4 --split holdout --label "Selected factor-offset settings holdout evaluation"
```

## Prefix-retention development evaluation (November 26, 2026 local time)

Run `20261127T051008Z-e1aa15ee`: 160 development puzzles, seeds 2026/2027/2028,
49 candidates per method, four workers, no time cutoff, no cache access. Both
methods were measured fresh. The baseline exactly reproduced the prior 49-candidate
instruction totals. All 960 programs validated and all six CSVs replayed successfully.

| Method | Seed 2026 | Seed 2027 | Seed 2028 | Mean summed task seconds per seed |
| --- | ---: | ---: | ---: | ---: |
| factor_offset | 64,143 | 64,148 | 64,161 | 369.12 |
| factor_prefix | 62,959 | 62,962 | 62,998 | 557.19 |

Savings were 1,184 / 1,186 / 1,163 instructions (1.81–1.85%). Prefix retention
won/tied/lost 120/20/20, 120/20/20, and 119/21/20 puzzles respectively. Worst
regressions were 23 instructions on each of practice_0149 and practice_0153.
It used about 1.51 times baseline's mean summed task time; full run wall time
was 697.7 seconds. Equal candidate caps do not equalize runtime.

Seed-2026 family totals:

| Family | Puzzles | factor_offset | factor_prefix | Saved |
| --- | ---: | ---: | ---: | ---: |
| independent | 38 | 22,871 | 22,792 | 79 |
| mixed | 40 | 19,641 | 19,315 | 326 |
| multiplicative | 29 | 7,535 | 7,041 | 494 |
| shared | 37 | 14,018 | 13,733 | 285 |
| tiny | 16 | 78 | 78 | 0 |

The full development result supports keeping prefix retention as an alternative,
but it is not a per-puzzle replacement for factor_offset. Holdout was not evaluated;
no combined export or cache update was produced. `factor_prefix` is explicitly
selectable through the common interface; default solve behavior is unchanged.

```powershell
python -m src.benchmark --methods factor_offset factor_prefix --seeds 2026 2027 2028 --candidates 49 --workers 4 --split train --label "Prefix retention full development comparison - 49 candidates"
python -m benchmarks.review_prefix_retention --run runs/<generated-run-id>
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
