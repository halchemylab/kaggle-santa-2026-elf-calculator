"""Validate a full CSV and print its total and per-puzzle instruction counts."""

import argparse
import csv
import json
from .io import load_puzzles, require_scored_ids
from .validator import validate


def score_submission(puzzles, path, *, competition=False):
    if competition:
        require_scored_ids(puzzles)
    scores, errors, seen = {}, [], set()
    with open(path, encoding='utf-8-sig', newline='') as stream:
        csv.field_size_limit(10_000_000)
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['id', 'program']:
            raise ValueError('CSV columns must be exactly id,program in that order')
        for number, row in enumerate(reader, 2):
            puzzle_id = row.get('id')
            try:
                if None in row or row.get('program') is None:
                    raise ValueError('Malformed CSV row')
                if puzzle_id in seen:
                    raise ValueError('Duplicate ID')
                seen.add(puzzle_id)
                if puzzle_id not in puzzles:
                    raise ValueError('Unknown ID')
                scores[puzzle_id] = validate(puzzles[puzzle_id], row['program'])
            except ValueError as error:
                errors.append(f'row {number} ({puzzle_id}): {error}')
    errors.extend(f'Missing ID: {key}' for key in sorted(set(puzzles) - seen))
    return scores, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--puzzles', required=True)
    parser.add_argument('--submission', required=True)
    parser.add_argument('--competition', action='store_true')
    parser.add_argument('--report', help='Optional JSON score report')
    args = parser.parse_args()
    scores, errors = score_submission(load_puzzles(args.puzzles), args.submission,
                                      competition=args.competition)
    for key, count in sorted(scores.items()):
        print(f'{key}: {count}')
    print('Worst 20:', sorted(scores.items(), key=lambda item: item[1], reverse=True)[:20])
    report = {'valid': not errors, 'total': sum(scores.values()) if not errors else None,
              'scores': scores, 'errors': errors}
    if args.report:
        from pathlib import Path
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2), encoding='utf-8')
    for error in errors:
        print('INVALID:', error)
    print(f'Total: {report["total"]}; valid programs: {len(scores)}; errors: {len(errors)}')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
