"""Replay candidate-budget artifacts and compare matching development puzzles."""

import json
from pathlib import Path
import statistics

from src.io import load_puzzles
from src.score import score_submission


def main():
    puzzles = load_puzzles('data/practice_puzzles.csv')
    reports = {}
    for path in sorted(Path('runs').glob('*/report.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        cap = report['budget']['max_candidates']
        if report['metadata'].get('label') == f'Factor-offset candidate budget {cap} development comparison':
            reports[cap] = (path.parent, report)
    assert set(reports) == {13, 25, 49}, 'All three budgets must finish before review'
    fingerprints = None
    reviewed = []
    previous_rows = None
    for cap in (13, 25, 49):
        directory, report = reports[cap]
        assert report['metadata']['split'] == 'train'
        assert report['metadata']['cache_updated'] is False
        assert report['seeds'] == [2026, 2027, 2028]
        assert report['budget']['seconds'] is None and report['workers'] == 4
        definitions = {p['id']: p['fingerprint'] for p in report['puzzles']}
        if fingerprints is None:
            fingerprints = definitions
        assert definitions == fingerprints
        subset = {key: puzzles[key] for key in definitions}
        assert all(subset[key].fingerprint() == value for key, value in definitions.items())
        assert len(subset) == 160
        rows = {(r['seed'], r['puzzle_id']): r for r in report['results']}
        assert len(rows) == 480 and all(r['valid'] for r in rows.values())
        totals = []
        for seed in report['seeds']:
            file = directory / report['program_files'][f'factor_offset:{seed}']
            scores, errors = score_submission(subset, file)
            assert not errors and set(scores) == set(subset), (file, errors)
            assert all(scores[key] == rows[(seed, key)]['steps'] for key in subset)
            totals.append(sum(scores.values()))
        comparison = {}
        if previous_rows is not None:
            for seed in report['seeds']:
                deltas = [previous_rows[(seed, key)]['steps'] - rows[(seed, key)]['steps']
                          for key in subset]
                assert all(delta >= 0 for delta in deltas), 'Nested search regressed'
                comparison[str(seed)] = {'saved': sum(deltas),
                                         'wins': sum(d > 0 for d in deltas),
                                         'ties': sum(d == 0 for d in deltas),
                                         'losses': sum(d < 0 for d in deltas)}
        item = {'candidates': cap, 'run_id': report['run_id'], 'seed_totals': totals,
                'mean_instructions': statistics.mean(totals),
                'wall_seconds': report['wall_seconds'],
                'mean_summed_task_seconds': statistics.mean(s['compute_seconds'] for s in report['summaries']),
                'programs_validated': len(rows), 'csvs_replayed': len(totals),
                'improvement_from_previous_budget': comparison}
        reviewed.append(item)
        previous_rows = rows
    output = Path('runs/factor_offset_candidate_budget_comparison.json')
    output.write_text(json.dumps(reviewed, indent=2), encoding='utf-8')
    print(json.dumps(reviewed, indent=2))


if __name__ == '__main__':
    main()
