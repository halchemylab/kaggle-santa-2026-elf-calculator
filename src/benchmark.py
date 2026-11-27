"""Reproducible fresh solver comparisons with independently validated artifacts."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
import uuid

from .cache import keep_best
from .io import load_puzzles, write_submission
from .solvers import METHODS, SearchBudget, solve
from .validator import validate


def dataset_fingerprint(puzzles):
    entries = [(key, p.fingerprint()) for key, p in sorted(puzzles.items())]
    return hashlib.sha256(json.dumps(entries).encode()).hexdigest()


def make_split(puzzles):
    ordered = sorted(puzzles, key=lambda key: hashlib.sha256(('santa-split-v1:' + key).encode()).hexdigest())
    count = max(1, len(ordered) // 5) if len(ordered) > 1 else 0
    return {'version': 1, 'dataset_fingerprint': dataset_fingerprint(puzzles),
            'train': sorted(ordered[count:]), 'holdout': sorted(ordered[:count])}


def select_split(puzzles, manifest, split):
    if manifest.get('dataset_fingerprint') != dataset_fingerprint(puzzles):
        raise ValueError('Split manifest does not match this dataset; create a new manifest')
    train, holdout = manifest['train'], manifest['holdout']
    if (len(set(train)) != len(train) or len(set(holdout)) != len(holdout)
            or set(train) & set(holdout) or set(train) | set(holdout) != set(puzzles)):
        raise ValueError('Split must contain every puzzle exactly once')
    ids = sorted(puzzles) if split == 'all' else manifest[split]
    if not ids:
        raise ValueError('Selected split is empty')
    return {key: puzzles[key] for key in ids}


def git_metadata():
    def git(*args):
        try:
            return subprocess.check_output(['git', *args], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    revision = git('rev-parse', 'HEAD')
    status = git('status', '--porcelain')
    return {'commit': revision, 'dirty': None if status is None else bool(status)}


def evaluate(task):
    puzzle, method, seed, budget = task
    started = time.perf_counter()
    row = {'puzzle_id': puzzle.id, 'fingerprint': puzzle.fingerprint(),
           'method': method, 'seed': seed, 'valid': False, 'steps': None,
           'error': None, 'candidates': 0, 'expansions': 0, 'notes': []}
    program = None
    try:
        solution = solve(puzzle, method, seed=seed, budget=budget)
        # The benchmark independently checks even a solver that says it validated.
        row['steps'] = validate(puzzle, solution.program)
        row.update(valid=True, candidates=solution.candidates, expansions=solution.expansions,
                   budget_exhausted=solution.budget_exhausted, notes=solution.notes)
        program = solution.program
    except Exception as error:
        row['error'] = f'{type(error).__name__}: {error}'
    row['seconds'] = time.perf_counter() - started
    return row, program


def summarize(rows, puzzle_ids):
    """Totals are comparable only when every expected puzzle validated."""
    expected = set(puzzle_ids)
    groups = {}
    for row in rows:
        groups.setdefault((row['method'], row['seed']), []).append(row)
    summaries = []
    for (method, seed), items in sorted(groups.items()):
        valid = [r for r in items if r['valid']]
        complete = len(items) == len(expected) and {r['puzzle_id'] for r in valid} == expected
        summaries.append({'method': method, 'seed': seed, 'valid': len(valid),
                          'expected': len(expected), 'complete': complete,
                          'total_steps': sum(r['steps'] for r in valid) if complete else None,
                          'compute_seconds': sum(r['seconds'] for r in items),
                          'errors': len(items) - len(valid)})
    winners = {}
    for row in rows:
        if row['valid'] and (row['puzzle_id'] not in winners
                or row['steps'] < winners[row['puzzle_id']]['steps']):
            winners[row['puzzle_id']] = row
    portfolio = {'complete': set(winners) == expected,
                 'total_steps': sum(r['steps'] for r in winners.values()) if set(winners) == expected else None,
                 'valid': len(winners), 'expected': len(expected)}
    return summaries, portfolio


def comparisons(rows):
    """Per-seed comparisons to binary; no partial-puzzle grand totals."""
    baselines = {(r['puzzle_id'], r['seed']): r for r in rows if r['method'] == 'binary'}
    groups = {}
    for row in rows:
        if row['method'] != 'binary':
            groups.setdefault((row['method'], row['seed']), []).append(row)
    result = []
    for (method, seed), items in sorted(groups.items()):
        pairs = [(r, baselines.get((r['puzzle_id'], seed))) for r in items]
        deltas = [(r['puzzle_id'], b['steps'] - r['steps']) for r, b in pairs
                  if r['valid'] and b and b['valid']]
        result.append({'method': method, 'seed': seed, 'compared': len(deltas),
                       'wins': sum(d > 0 for _, d in deltas),
                       'ties': sum(d == 0 for _, d in deltas),
                       'losses': sum(d < 0 for _, d in deltas),
                       'steps_saved': sum(d for _, d in deltas) if len(deltas) == len(items) else None,
                       'largest_savings': sorted(deltas, key=lambda x: (-x[1], x[0]))[:10],
                       'largest_regressions': sorted(((p, d) for p, d in deltas if d < 0),
                                                      key=lambda x: (x[1], x[0]))[:10]})
    return result


def seed_statistics(summaries):
    result = []
    for method in sorted({s['method'] for s in summaries}):
        items = [s for s in summaries if s['method'] == method]
        totals = [s['total_steps'] for s in items if s['complete']]
        complete = len(totals) == len(items)
        result.append({'method': method, 'seeds': len(items), 'complete_seeds': len(totals),
                       'mean_steps': statistics.mean(totals) if complete else None,
                       'min_steps': min(totals) if complete else None,
                       'max_steps': max(totals) if complete else None,
                       'stdev_steps': statistics.pstdev(totals) if complete else None})
    return result


def run_benchmark(puzzles, *, methods, seeds, budget, run_dir, workers=1,
                  metadata=None, update_cache=None):
    if not methods or any(m not in METHODS for m in methods) or not seeds:
        raise ValueError('Select known methods and at least one seed')
    if len(set(methods)) != len(methods) or len(set(seeds)) != len(seeds):
        raise ValueError('Methods and seeds must be unique')
    if workers < 1 or not puzzles:
        raise ValueError('Positive workers and nonempty puzzles required')
    directory = Path(run_dir)
    directory.mkdir(parents=True, exist_ok=False)
    # Preserve the actual implementation even when benchmarking uncommitted work.
    source_files = sorted(p for p in Path(__file__).parent.iterdir() if p.suffix in ('.py', '.html'))
    source_hashes = {}
    for source in source_files:
        content = source.read_bytes()
        source_hashes[source.name] = hashlib.sha256(content).hexdigest()
        (directory / 'source').mkdir(exist_ok=True)
        (directory / 'source' / source.name).write_bytes(content)
    started = time.perf_counter()
    rows, programs = [], {}
    tasks = [(puzzle, method, seed, budget) for method in methods
             for seed in seeds for puzzle in puzzles.values()]

    def collect(results):
        for index, (row, program) in enumerate(results, 1):
            rows.append(row)
            if row['valid']:
                programs.setdefault((row['method'], row['seed']), {})[row['puzzle_id']] = program
                if update_cache is not None:
                    keep_best(update_cache, puzzles[row['puzzle_id']], program)
            if index % 100 == 0 or index == len(tasks):
                print(f'Benchmark: {index}/{len(tasks)} evaluated', flush=True)

    if workers == 1:
        collect(map(evaluate, tasks))
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            collect(executor.map(evaluate, tasks))
    artifacts = {}
    for (method, seed), batch in programs.items():
        if set(batch) == set(puzzles):
            relative = f'programs/{method}_seed_{seed}.csv'
            write_submission(directory / relative, puzzles, batch)
            artifacts[f'{method}:{seed}'] = relative
    summaries, portfolio = summarize(rows, puzzles)
    report = {'schema_version': 1, 'run_id': directory.name,
              'created_at': datetime.now(timezone.utc).isoformat(),
              'metadata': {**(metadata or {}), 'initial_targets_count': True},
              'budget': asdict(budget), 'workers': workers,
              'methods': list(methods), 'seeds': list(seeds),
              'wall_seconds': time.perf_counter() - started,
              'puzzles': [{'id': p.id, 'fingerprint': p.fingerprint(),
                           'targets': len(p.targets), 'max_target': str(max(p.targets))}
                          for p in puzzles.values()],
              'summaries': summaries, 'portfolio': portfolio,
              'comparisons_to_binary': comparisons(rows), 'seed_statistics': seed_statistics(summaries),
              'source_hashes': source_hashes,
              'program_files': artifacts, 'results': rows}
    (directory / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--puzzles', default='data/practice_puzzles.csv')
    parser.add_argument('--methods', nargs='+', choices=METHODS, default=list(METHODS))
    parser.add_argument('--seeds', nargs='+', type=int, default=[2026, 2027, 2028])
    parser.add_argument('--candidates', type=int, default=13)
    parser.add_argument('--seconds', type=float, help='Soft per-puzzle search limit, after completing fallback')
    parser.add_argument('--beam-width', type=int, default=24)
    parser.add_argument('--beam-depth', type=int, default=10)
    parser.add_argument('--beam-expansions', type=int, default=250)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--runs', default='runs')
    parser.add_argument('--split-file', default='benchmarks/practice_split.json')
    parser.add_argument('--split', choices=['train', 'holdout', 'all'], default='train')
    parser.add_argument('--label', default='', help='Human-readable experiment description')
    parser.add_argument('--update-cache', metavar='DIRECTORY', help='Optional validated best-cache updates')
    args = parser.parse_args()
    puzzles = load_puzzles(args.puzzles)
    split_path = Path(args.split_file)
    if split_path.exists():
        manifest = json.loads(split_path.read_text(encoding='utf-8'))
    else:
        manifest = make_split(puzzles)
        split_path.parent.mkdir(parents=True, exist_ok=True)
        split_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    selected = select_split(puzzles, manifest, args.split)
    metadata = {'label': args.label, 'dataset_path': args.puzzles,
                'initial_targets_count': True,
                'dataset_fingerprint': dataset_fingerprint(puzzles), 'split': args.split,
                'split_file': str(split_path), 'git': git_metadata(),
                'python': platform.python_version(), 'platform': platform.platform(),
                'timing': 'Includes fallback and validation; summed task times overlap with multiple workers.',
                'budget_policy': 'Cooperative: complete fallback; check time between candidates or beam expansions.',
                'cache_updated': args.update_cache is not None}
    budget = SearchBudget(args.candidates, args.seconds, args.beam_width,
                          args.beam_depth, args.beam_expansions)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    report = run_benchmark(selected, methods=args.methods, seeds=args.seeds, budget=budget,
                           run_dir=Path(args.runs) / run_id, workers=args.workers,
                           metadata=metadata, update_cache=args.update_cache)
    from .dashboard import build_dashboard
    dashboard = build_dashboard(args.runs)
    print(json.dumps({'run_id': run_id, 'summaries': report['summaries'],
                      'portfolio': report['portfolio'], 'wall_seconds': report['wall_seconds'],
                      'dashboard': str(dashboard)}, indent=2))
    raise SystemExit(any(not row['valid'] for row in report['results']))


if __name__ == '__main__':
    main()
