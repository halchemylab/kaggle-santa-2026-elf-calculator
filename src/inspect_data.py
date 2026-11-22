"""Print a compact schema and magnitude summary without publishing dataset rows."""

import argparse
import csv
import json
from collections import Counter
from .io import load_puzzles


def summarize(path):
    puzzles = list(load_puzzles(path).values())
    def span(values):
        values = list(values)
        return [min(values), max(values)]
    with open(path, encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    return {'file': str(path), 'rows': len(puzzles), 'columns': list(rows[0]),
            'target_count_range': span(len(p.targets) for p in puzzles),
            'target_range': span(t for p in puzzles for t in p.targets),
            'start_count_range': span(len(p.starting_values) for p in puzzles),
            'start_value_range': span(t for p in puzzles for t in p.starting_values),
            'value_limit_range': span(p.value_limit for p in puzzles),
            'families': dict(Counter(row.get('family', 'unspecified') for row in rows)),
            'design_tiers': dict(Counter(row.get('design_tier', 'unspecified') for row in rows))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()
    for path in args.paths:
        print(json.dumps(summarize(path), indent=2))
