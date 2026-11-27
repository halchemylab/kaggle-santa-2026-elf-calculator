"""A diagnostic ablation on nine selected development puzzles, not holdout tuning."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from src import solvers
from src.benchmark import select_split
from src.io import load_puzzles
from src.validator import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('runs/program_diagnosis'),
                        help='Directory containing audit.json and receiving probe results')
    args = parser.parse_args()
    out = args.output
    audit = json.loads((out / 'audit.json').read_text())
    ids = audit['summary']['selected_puzzles']
    puzzles = load_puzzles('data/practice_puzzles.csv')
    manifest = json.loads(Path('benchmarks/practice_split.json').read_text(encoding='utf-8'))
    train = select_split(puzzles, manifest, 'train')
    assert set(audit['puzzles']) == set(train), 'Probe requires the frozen development audit'
    assert all(audit['puzzles'][key]['fingerprint'] == p.fingerprint() for key, p in train.items())
    assert all(audit['puzzles'][key]['id'] == key for key in ids)
    seed = audit['summary']['seed']
    budget = solvers.SearchBudget(**audit['summary']['budget'])
    assert budget.seconds is None, 'Use a reproducible candidate count, not a time cutoff'
    source = Path('src/greedy.py').read_text(encoding='utf-8')
    results = []
    for key in ids:
        p = puzzles[key]
        timings, solutions = {}, {}
        for method in ('baseline', 'retain_prefixes'):
            started = time.perf_counter()
            solver_method = 'factor_offset' if method == 'baseline' else 'factor_prefix'
            solution = solvers.solve(p, solver_method, seed=seed, budget=budget)
            steps = validate(p, solution.program)
            timings[method] = time.perf_counter() - started
            solutions[method] = steps
        assert solutions['baseline'] == audit['puzzles'][key]['steps']
        row = {'id': key, 'family': audit['puzzles'][key]['family'],
               **solutions, 'saved': solutions['baseline'] - solutions['retain_prefixes'],
               'seconds': timings, 'fingerprint': p.fingerprint()}
        results.append(row)
        print(json.dumps(row), flush=True)
    report = {'description': 'Exploratory matched ablation on nine selected development puzzles',
              'method': 'factor_offset', 'seed': seed, 'candidates': budget.max_candidates, 'workers': 1,
              'baseline_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'variant_method': 'factor_prefix',
              'change': 'Allocate a destination for each base digit rather than overwriting every prefix in one register',
              'results': results, 'total_saved': sum(r['saved'] for r in results)}
    (out / 'prefix_retention_ablation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('TOTAL SAVED:', report['total_saved'])


if __name__ == '__main__':
    main()
