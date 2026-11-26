"""Inspect saved development programs; this is not a fresh solver benchmark."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from src.greedy import apply
from src.benchmark import select_split
from src.io import load_puzzles
from src.validator import validate

def inspect(puzzle, program):
    validate(puzzle, program)
    values = [None] * 48
    values[:len(puzzle.starting_values)] = puzzle.starting_values
    producers = [None] * 48
    dependencies, roots, first_targets = [], [], {}
    generated = Counter()
    duplicate_results = 0
    evicted_reconstructions = 0
    last_loss = {}
    reconstruction_reasons = Counter()
    used_registers = set(range(len(puzzle.starting_values)))
    target_set = set(puzzle.targets)
    segments, segment_start = [], 0
    operations = Counter()
    rows = []
    for i, (op, a, b, dst) in enumerate(program):
        x, y = values[a], values[b]
        value = apply(op, x, y)
        dependencies.append([p for p in (producers[a], producers[b]) if p is not None])
        duplicate_results += value in values
        evicted_reconstructions += generated[value] > 0 and value not in values
        if generated[value] > 0 and value not in values:
            reconstruction_reasons[last_loss.get(value, 'unknown')] += 1
        generated[value] += 1
        operations[op] += 1
        if value in target_set and value not in first_targets:
            first_targets[value] = i
            roots.append(i)
            segments.append({'target': str(value), 'first_production_step': i + 1,
                             'steps_since_previous_target': i + 1 - segment_start})
            segment_start = i + 1
        rows.append({'step': i + 1, 'op': op, 'left': str(x), 'right': str(y),
                     'result': str(value), 'destination': dst})
        old_value = values[dst]
        if old_value is not None and old_value != value and values.count(old_value) == 1:
            last_loss[old_value] = 'source_overwritten' if dst in (a, b) else 'other_destination_overwritten'
        values[dst] = value
        producers[dst] = i
        used_registers.add(dst)
    live, pending = set(), list(roots)
    while pending:
        i = pending.pop()
        if i not in live:
            live.add(i)
            pending.extend(dependencies[i])
    pruned = [instruction for i, instruction in enumerate(program) if i in live]
    validate(puzzle, pruned)
    return {'steps': len(program), 'targets': len(target_set), 'operations': dict(operations),
            'removable_steps': len(program) - len(pruned),
            'duplicate_results': duplicate_results,
            'evicted_value_reconstructions': evicted_reconstructions,
            'reconstruction_reasons': dict(reconstruction_reasons),
            'registers_used': len(used_registers),
            'segments': segments, 'arithmetic_trace': rows}, pruned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='Development benchmark directory')
    parser.add_argument('--output', type=Path, default=Path('runs/program_diagnosis'))
    parser.add_argument('--seed', type=int, default=2026)
    args = parser.parse_args()
    puzzles = load_puzzles('data/practice_puzzles.csv')
    with open('data/practice_puzzles.csv', encoding='utf-8-sig', newline='') as stream:
        metadata = {row['id']: row for row in csv.DictReader(stream)}
    report = json.loads((args.run / 'report.json').read_text(encoding='utf-8'))
    assert report['metadata']['split'] == 'train'
    manifest = json.loads(Path('benchmarks/practice_split.json').read_text(encoding='utf-8'))
    train = select_split(puzzles, manifest, 'train')
    ids = {p['id']: p['fingerprint'] for p in report['puzzles']}
    assert set(ids) == set(train), 'Only the frozen development split may be diagnosed'
    assert all(puzzles[key].fingerprint() == fingerprint for key, fingerprint in ids.items())
    with (args.run / report['program_files'][f'factor_offset:{args.seed}']).open(encoding='utf-8', newline='') as stream:
        programs = {row['id']: json.loads(row['program']) for row in csv.DictReader(stream)}
    assert set(programs) == set(ids)
    audits = {}
    for key, program in programs.items():
        audit, _ = inspect(puzzles[key], program)
        audit.update(id=key, fingerprint=puzzles[key].fingerprint(),
                     family=metadata[key]['family'], tier=metadata[key]['design_tier'])
        audits[key] = audit
    families = defaultdict(list)
    for audit in audits.values():
        families[audit['family']].append(audit)
    ranked = sorted(audits, key=lambda key: (-audits[key]['steps'], key))
    selected = ranked[:5]
    for family in sorted(families):
        if family != 'independent':
            selected.append(next(key for key in ranked if audits[key]['family'] == family))
    summary = {'source_run': args.run.name, 'seed': args.seed, 'budget': report['budget'],
               'description': 'Saved-program inspection, not a fresh benchmark; holdout excluded',
               'total_steps': sum(a['steps'] for a in audits.values()),
               'removable_steps': sum(a['removable_steps'] for a in audits.values()),
               'evicted_value_reconstructions': sum(a['evicted_value_reconstructions'] for a in audits.values()),
               'families': {name: {'puzzles': len(items), 'steps': sum(a['steps'] for a in items),
                                   'targets': sum(a['targets'] for a in items),
                                   'removable_steps': sum(a['removable_steps'] for a in items),
                                   'evicted_value_reconstructions': sum(a['evicted_value_reconstructions'] for a in items)}
                            for name, items in families.items()},
               'selected_puzzles': selected}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'audit.json').write_text(json.dumps({'summary': summary, 'puzzles': audits}, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    for key in selected:
        print(json.dumps({k: v for k, v in audits[key].items() if k not in ('segments', 'arithmetic_trace')}))


if __name__ == '__main__':
    main()
