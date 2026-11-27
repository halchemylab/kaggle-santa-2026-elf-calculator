# Pick up here next session

## Final checkpoint: project closed November 27, 2026

The user chose to stop after the first successful Kaggle submission. Kaggle
reported `scored_first.csv` as Complete with score **392,980**, matching the local
validator exactly. This was an independently developed submission; no public
solution programs were imported. No further experiments are planned. The notes
below preserve possible future work only if the user decides to return.

The validator, greedy solver, benchmark runner, and offline dashboard are implemented.
See README.md for commands and docs/benchmarking.md for experiment definitions.

## Latest session: November 27 official data and rules

`data/puzzles.csv` and `data/sample_submission.csv` are present locally and ignored
by Git. The user supplied the official Data rules: starts initialize consecutive
registers, matching targets count as covered immediately, and coverage survives
overwrites. Validator, construction solvers, and beam search now follow that rule.
The official sample passes all 1,000 puzzles: 1,490,379 instructions, maximum
2,873. All 40 tests pass, including the formerly skipped official-sample test.

New benchmark reports label `initial_targets_count: true`; older reports without
the field used the conservative policy. The dashboard blocks comparisons across
coverage policies. Recreate baseline runs before future tuning; do not attribute
coverage-rule savings to an algorithm change. The frozen puzzle split is unchanged.

The first scored export uses factor_prefix, 13 candidates, seed 2026, four workers,
and isolated cache/scored_factor_prefix_13. See README for reproduction commands.
Generated `submissions/scored_first.csv`: all 1,000 programs independently
validated, 392,980 instructions, maximum 814 per program, 230.1 seconds solve wall
time. This is 73.63% fewer instructions than the official sample. Validation report:
`submissions/scored_first_validation.json`. The user uploaded this file and
reported Kaggle acceptance at exactly 392,980. The submission description was
"First validated submission - prefix retention, 392980 instructions". Do not
upload practice files or edit the generated CSV in Excel.

## Latest session: November 26 prefix-retention evaluation

Implemented optional `factor_prefix` and evaluated it against fresh `factor_offset`
on all 160 development puzzles: 49 candidates, seeds 2026/2027/2028, four workers,
no cutoff and no cache access. Run `20261127T051008Z-e1aa15ee`:

| Method | Seed 2026 | Seed 2027 | Seed 2028 |
| --- | ---: | ---: | ---: |
| factor_offset | 64,143 | 64,148 | 64,161 |
| factor_prefix | 62,959 | 62,962 | 62,998 |

Prefix retention saved 1,163–1,186 instructions (1.81–1.85%), with mean summed
task time about 1.51 times baseline. Per seed: 119–120 wins, 20–21 ties, and
20 losses. Worst losses were +23 instructions on practice_0149 and practice_0153.
Multiplicative puzzles improved most (all 29 improved; 6.27–6.56% total savings);
independent puzzles improved only about 0.35% in total and had 12 regressions.
All 960 programs and six exported CSVs validated. Tests: 38 passed, one official
sample skip; dashboard smoke check passed. Holdout was untouched.

The method remains optional; defaults and the factor_offset construction are
unchanged. No combined export or cache update was created. For regression/family
details, run `python -m benchmarks.review_prefix_retention --run runs/<run-id>`.

Next: inspect the 20 regressions before adopting the new method. Retaining more
prefixes helps overall but can displace useful operands. Either improve that
tradeoff on development or deliberately budget both methods as alternatives;
do not silently double a method's candidate budget or tune on holdout.

## Latest session: November 25 diagnostics

Factor/offset candidate budgets of 13, 25, and 49 were compared on development
only, with seeds 2026/2027/2028 and four workers. Totals were respectively
64,294/64,290/64,309; 64,193/64,209/64,226; and 64,143/64,148/64,161.
Going from 13 to 49 saved about 0.23% for about 3.9 times the wall time.
All 1,440 programs and nine CSVs validated. No new holdout evaluation occurred.
The combined-seed export was removed at the user's request; do not recreate it
without a new request.

The 49-candidate seed-2026 audit found only 10 dependency-prunable instructions
out of 64,143, but 2,452 recreations of previously generated and lost values.
An isolated prefix-retention probe improved eight of nine selected puzzles and
tied one: 5,677 to 5,601 instructions (1.34%). This is a deliberately selected
sample, not a demonstrated full-set gain. Production solver behavior is unchanged.

Next solver experiment: evaluate prefix retention as a separate candidate on
all development puzzles with matched settings and regression checks. Do not tune
on holdout. See [diagnostic findings and reproduction commands](program_diagnosis.txt).
Scripts live in `benchmarks/`; generated artifacts remain ignored under `runs/`.

## Latest experiment: factor/offset construction

Implemented `factor_offset` in the common solver interface. On the 160 development
puzzles, with seeds 2026–2028 and 13 candidates, it used 64,294 / 64,290 / 64,309
instructions versus greedy's 74,030 per seed: about 13.15% fewer. Each seed improved
144 puzzles, tied 16, and regressed on none. All 1,920 programs and all exported
CSVs validated. Mean summed task time was about 2.2 times greedy's in this run.
Run: `20261122T210642Z-9ed33410`; wall time 148.3 seconds. Holdout untouched.

The November 24 post-pull development rerun exactly reproduced these scores.
The selected settings were then evaluated on holdout (run
`20261125T041327Z-2f0ea9b9`): factor/offset used 17,700 / 17,673 / 17,675
instructions versus greedy's 20,493 per seed, improving all 40 puzzles in every
seed (13.63–13.76% fewer instructions). All 240 programs and six CSVs validated.
The holdout has now been evaluated; do not tune against it.

`src.solve --method factor_offset --candidates 13 --seed 2026 --workers 4`
now exposes the common solver interface for cache updates and validated export.
Commands without `--method` retain the historical greedy behavior.

The full 200-puzzle practice export at seed 2026 was generated as
`submissions/practice_factor_offset_v1.csv`: 81,994 instructions, all 200 programs
independently replayed successfully. This is a practice artifact, not a competition
submission. Tests: 35 passed, one official-sample skip; dashboard smoke check passed
with both development and holdout runs in history. Local artifacts remain ignored.

Next: obtain the official scored puzzles and sample, confirm the open rule
assumptions, and validate the sample before producing a scored submission.
Further algorithm experiments should be selected using development puzzles.

## Resume

1. Pull the latest code. Practice puzzles and the fixed split are included.
2. Open `runs/dashboard.html` on this computer. On a different computer, generate
   local run records first with `python -m src.benchmark --workers 4 --label "Resume baseline"`.
   Past runs, generated dashboards, submissions, and caches are local and ignored.
3. Compare `base_expansion` as reference against `greedy`, with the same seed/run.
   Inspect the puzzles that improved or regressed. Visually check the dashboard:
   interaction tests passed, but no browser was connected for layout inspection.
4. Factor/offset has passed development and holdout evaluation. Benchmark further
   changes on the development split with the same settings and seeds, and inspect
   both instruction savings and added runtime.
5. Keep holdout results as the frozen selected-settings evaluation. Learning-guided
   search can come later, once we have useful search examples.

## Current reference results

The initial four-method run evaluated 160 development puzzles, three seeds, and
13 construction candidates with four workers. All 1,920 programs validated.

- Binary: 226,626 instructions per seed.
- Larger-base construction: 74,136 per seed.
- Greedy: 74,030 per seed.
- Tiny-puzzle beam plus binary fallback: 226,571 per seed.
- Combined best-per-puzzle portfolio: 74,008 instructions.

Most improvement came from larger-base construction; the immediate-target greedy
scan saved another 106 net steps. The current beam is restricted to tiny puzzles
and does not test its potential on the large puzzles. These are practice results,
not optimality proofs or leaderboard scores.

The official scored CSV and sample are now local. The latest-session section
above supersedes the earlier absence and initialization assumptions.

Suggested next prompt:

> Read AGENTS.md, docs/next_session.md, and docs/program_diagnosis.txt. Review the
> full prefix-retention results and diagnose the 20 per-seed regressions before
> choosing the next development experiment. Leave holdout untouched.
