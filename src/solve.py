"""Solve puzzles in parallel, preserve best programs, and export a validated CSV."""

import argparse
import json
import time
from dataclasses import asdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from .cache import keep_best
from .greedy import best_program, solve_one
from .io import load_puzzles, require_scored_ids, write_submission
from .solvers import METHODS, SearchBudget, solve


def worker(task):
    puzzle, restarts, seed, bases, method, budget = task
    baseline = solve_one(puzzle, base=2, greedy=False)
    if method is None:
        candidate = best_program(puzzle, restarts=restarts, seed=seed, bases=bases)
    else:
        candidate = solve(puzzle, method, seed=seed, budget=budget).program
    return puzzle.id, len(baseline), candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--puzzles', default='data/practice_puzzles.csv')
    parser.add_argument('--output', help='Defaults to submissions/practice_<method>_v1.csv')
    parser.add_argument('--cache', default='cache/best')
    parser.add_argument('--report', default='submissions/solve_report.json')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--method', choices=METHODS, help='Use the common benchmark solver interface')
    parser.add_argument('--candidates', type=int, help='Common solver candidate cap (default: 13)')
    parser.add_argument('--restarts', type=int)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--bases', type=int, nargs='+', choices=[2, 4, 8, 16])
    parser.add_argument('--competition', action='store_true')
    args = parser.parse_args()
    if args.method is not None and (args.restarts is not None or args.bases is not None):
        parser.error('--method uses --candidates; --restarts and --bases are legacy-only')
    if args.method is None and args.candidates is not None:
        parser.error('--candidates requires --method')
    args.restarts = 2 if args.restarts is None else args.restarts
    args.bases = [4, 8, 16] if args.bases is None else args.bases
    if args.workers < 1 or args.restarts < 0:
        parser.error('workers must be positive and restarts must be nonnegative')
    try:
        budget = SearchBudget(max_candidates=13 if args.candidates is None else args.candidates)
    except ValueError as error:
        parser.error(str(error))
    if args.competition and args.output is None:
        parser.error('--competition requires an explicit --output path')
    args.output = args.output or f'submissions/practice_{args.method or "greedy"}_v1.csv'
    puzzles = load_puzzles(args.puzzles)
    if args.competition:
        require_scored_ids(puzzles)
    started = time.perf_counter()
    # Explicit methods use the same per-puzzle seed as the benchmark. Preserve
    # the historical seed schedule for invocations without --method.
    tasks = [(p, args.restarts, args.seed if args.method else args.seed + index,
              args.bases, args.method, budget)
             for index, p in enumerate(puzzles.values())]
    programs, baselines = {}, {}

    def collect(results):
        for index, (key, baseline, candidate) in enumerate(results, 1):
            programs[key] = keep_best(args.cache, puzzles[key], candidate)
            baselines[key] = baseline
            if index % 20 == 0 or index == len(puzzles):
                print(f'{index}/{len(puzzles)} solved', flush=True)

    if args.workers == 1:
        collect(map(worker, tasks))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            collect(executor.map(worker, tasks))
    write_submission(args.output, puzzles, programs, competition=args.competition)
    scores = {key: len(program) for key, program in programs.items()}
    report = {'puzzle_file': str(args.puzzles), 'puzzle_count': len(puzzles),
              'initial_targets_count': True,
              'competition': args.competition, 'binary_baseline_total': sum(baselines.values()),
              'best_total': sum(scores.values()), 'runtime_seconds': time.perf_counter() - started,
              'seed': args.seed, 'bases': args.bases if args.method is None else None,
              'restarts': args.restarts if args.method is None else None,
              'method': args.method or 'greedy',
              'solver_interface': 'common' if args.method else 'legacy',
              'budget': asdict(budget) if args.method else None,
              'scores': scores, 'baseline_scores': baselines,
              'worst_20': sorted(scores.items(), key=lambda item: item[1], reverse=True)[:20]}
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('scores', 'baseline_scores')}, indent=2))


if __name__ == '__main__':
    main()
