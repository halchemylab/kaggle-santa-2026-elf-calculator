"""Replay both methods and summarize a matched development-only comparison."""

import argparse
import csv
import json
from pathlib import Path
import statistics

from src.benchmark import select_split
from src.io import load_puzzles
from src.score import score_submission


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.run / 'report.json').read_text(encoding='utf-8'))
    assert report['metadata']['split'] == 'train'
    assert report['metadata']['cache_updated'] is False
    assert set(report['methods']) == {'factor_offset', 'factor_prefix'}
    puzzles = load_puzzles(report['metadata']['dataset_path'])
    manifest = json.loads(Path(report['metadata']['split_file']).read_text(encoding='utf-8'))
    train = select_split(puzzles, manifest, 'train')
    definitions = {p['id']: p['fingerprint'] for p in report['puzzles']}
    assert definitions == {key: p.fingerprint() for key, p in train.items()}
    with open(report['metadata']['dataset_path'], encoding='utf-8-sig', newline='') as stream:
        metadata = {r['id']: r for r in csv.DictReader(stream)}
    rows = {(r['method'], r['seed'], r['puzzle_id']): r for r in report['results']}
    assert len(rows) == len(train) * len(report['methods']) * len(report['seeds'])
    assert all(r['valid'] for r in rows.values())
    csv_count = 0
    for method in report['methods']:
        for seed in report['seeds']:
            path = args.run / report['program_files'][f'{method}:{seed}']
            scores, errors = score_submission(train, path)
            assert not errors and set(scores) == set(train), (path, errors)
            assert all(scores[key] == rows[(method, seed, key)]['steps'] for key in train)
            csv_count += 1
    summaries = []
    for seed in report['seeds']:
        paired = []
        for key in train:
            old, new = rows[('factor_offset', seed, key)], rows[('factor_prefix', seed, key)]
            paired.append({'id': key, 'family': metadata[key]['family'],
                           'baseline': old['steps'], 'prefix': new['steps'],
                           'saved': old['steps'] - new['steps']})
        family_totals = {}
        for family in sorted({r['family'] for r in paired}):
            members = [r for r in paired if r['family'] == family]
            family_totals[family] = {
                'puzzles': len(members), 'baseline': sum(r['baseline'] for r in members),
                'prefix': sum(r['prefix'] for r in members), 'saved': sum(r['saved'] for r in members),
                'wins': sum(r['saved'] > 0 for r in members),
                'ties': sum(r['saved'] == 0 for r in members),
                'losses': sum(r['saved'] < 0 for r in members)}
        old_total, new_total = (sum(r[k] for r in paired) for k in ('baseline', 'prefix'))
        times = {method: sum(rows[(method, seed, key)]['seconds'] for key in train)
                 for method in report['methods']}
        summaries.append({'seed': seed, 'baseline': old_total, 'prefix': new_total,
                          'saved': old_total - new_total,
                          'percent_saved': (old_total - new_total) * 100 / old_total,
                          'wins': sum(r['saved'] > 0 for r in paired),
                          'ties': sum(r['saved'] == 0 for r in paired),
                          'losses': sum(r['saved'] < 0 for r in paired),
                          'summed_task_seconds': times,
                          'families': family_totals,
                          'largest_savings': sorted(paired, key=lambda r: (-r['saved'], r['id']))[:10],
                          'regressions': sorted((r for r in paired if r['saved'] < 0),
                                                key=lambda r: (r['saved'], r['id']))})
    means = {method: statistics.mean(s['summed_task_seconds'][method] for s in summaries)
             for method in report['methods']}
    output = {'run_id': report['run_id'], 'budget': report['budget'],
              'workers': report['workers'], 'wall_seconds': report['wall_seconds'],
              'programs_validated': len(rows), 'csvs_replayed': csv_count,
              'mean_summed_task_seconds': means,
              'runtime_ratio': means['factor_prefix'] / means['factor_offset'],
              'summaries': summaries}
    (args.run / 'prefix_comparison.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
