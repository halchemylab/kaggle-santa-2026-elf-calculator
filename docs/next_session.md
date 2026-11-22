# Pick up here next session

The validator, greedy solver, benchmark runner, and offline dashboard are implemented.
See README.md for commands and docs/benchmarking.md for experiment definitions.

## Latest experiment: factor/offset construction

Implemented `factor_offset` in the common solver interface. On the 160 development
puzzles, with seeds 2026–2028 and 13 candidates, it used 64,294 / 64,290 / 64,309
instructions versus greedy's 74,030 per seed: about 13.15% fewer. Each seed improved
144 puzzles, tied 16, and regressed on none. All 1,920 programs and all exported
CSVs validated. Mean summed task time was about 2.2 times greedy's in this run.
Run: `20261122T210642Z-9ed33410`; wall time 148.3 seconds. Holdout untouched.

Next: inspect these development results, decide whether to keep the settings,
then evaluate holdout explicitly. If adopting the method for export, expose the
common solver interface in `src.solve`, which still uses the original greedy.

## Resume

1. Pull the latest code. Practice puzzles and the fixed split are included.
2. Open `runs/dashboard.html` on this computer. On a different computer, generate
   local run records first with `python -m src.benchmark --workers 4 --label "Resume baseline"`.
   Past runs, generated dashboards, submissions, and caches are local and ignored.
3. Compare `base_expansion` as reference against `greedy`, with the same seed/run.
   Inspect the puzzles that improved or regressed. Visually check the dashboard:
   interaction tests passed, but no browser was connected for layout inspection.
4. Review the implemented factor/offset method against greedy. Benchmark further
   changes on the development split with the same
   settings and seeds, and inspect both instruction savings and added runtime.
5. Keep the 40-puzzle holdout for evaluation after selecting the new settings.
   Learning-guided search can come later, once we have useful search examples.

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

The official scored puzzle CSV and sample submission are still absent. Before a
competition submission, obtain them and confirm register initialization and initial
target coverage against the Data rules. Work on practice algorithms can continue.

Suggested next prompt:

> Read AGENTS.md and docs/next_session.md. Review factor_offset versus greedy on
> the development split and help select the next experiment. Leave the holdout
> untouched unless we explicitly choose to evaluate the selected settings.
