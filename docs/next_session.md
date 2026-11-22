# Pick up here next session

The validator, greedy solver, benchmark runner, and offline dashboard are implemented.
See README.md for commands and docs/benchmarking.md for experiment definitions.

## Resume

1. Pull the latest code. Practice puzzles and the fixed split are included.
2. Open `runs/dashboard.html` on this computer. On a different computer, generate
   local run records first with `python -m src.benchmark --workers 4 --label "Resume baseline"`.
   Past runs, generated dashboards, submissions, and caches are local and ignored.
3. Compare `base_expansion` as reference against `greedy`, with the same seed/run.
   Inspect the puzzles that improved or regressed. Visually check the dashboard:
   interaction tests passed, but no browser was connected for layout inspection.
4. Choose one focused improvement, such as constructing targets from factors or
   offsets of retained values. Benchmark on the development split with the same
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

> Read AGENTS.md and docs/next_session.md. Help me inspect base_expansion versus
> greedy on the development split, then implement one targeted improvement and
> compare it under the same benchmark settings. Leave the holdout untouched.
