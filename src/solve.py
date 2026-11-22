"""Solve puzzles in parallel, preserve best programs, and export a validated CSV."""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from .cache import keep_best
from .greedy import best_program, solve_one
from .io import load_puzzles, require_scored_ids, write_submission


def worker(task):
    puzzle, restarts, seed, bases = task
    baseline = solve_one(puzzle, base=2, greedy=False)
    candidate = best_program(puzzle, restarts=restarts, seed=seed, bases=bases)
    return puzzle.id, len(baseline), candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--puzzles', default='data/practice_puzzles.csv')
    parser.add_argument('--output', default='submissions/practice_greedy_v1.csv')
    parser.add_argument('--cache', default='cache/best')
    parser.add_argument('--report', default='submissions/solve_report.json')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--restarts', type=int, default=2)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--bases', type=int, nargs='+', default=[4, 8, 16], choices=[2, 4, 8, 16])
    parser.add_argument('--competition', action='store_true')
    args = parser.parse_args()
    if args.workers < 1 or args.restarts < 0:
        parser.error('workers must be positive and restarts must be nonnegative')
    puzzles = load_puzzles(args.puzzles)
    if args.competition:
        require_scored_ids(puzzles)
    started = time.perf_counter()
    tasks = [(p, args.restarts, args.seed + index, args.bases)
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
              'competition': args.competition, 'binary_baseline_total': sum(baselines.values()),
              'best_total': sum(scores.values()), 'runtime_seconds': time.perf_counter() - started,
              'seed': args.seed, 'bases': args.bases, 'restarts': args.restarts,
              'scores': scores, 'baseline_scores': baselines,
              'worst_20': sorted(scores.items(), key=lambda item: item[1], reverse=True)[:20]}
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('scores', 'baseline_scores')}, indent=2))


if __name__ == '__main__':
    main()
