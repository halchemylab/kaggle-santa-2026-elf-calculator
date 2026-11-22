"""Puzzle parsing and correctly escaped, validated submission writing."""

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Puzzle:
    id: str
    starting_values: tuple[int, ...]
    targets: tuple[int, ...]
    value_limit: int
    registers: int = 48

    def __post_init__(self):
        if not self.id or type(self.registers) is not int or self.registers != 48:
            raise ValueError('Expected an ID and exactly 48 registers')
        if type(self.value_limit) is not int or self.value_limit < 1:
            raise ValueError(f'{self.id}: invalid value_limit')
        if not 1 <= len(self.starting_values) <= self.registers or not self.targets:
            raise ValueError(f'{self.id}: invalid starts or empty targets')
        if any(type(v) is not int or not 1 <= v <= self.value_limit
               for v in (*self.starting_values, *self.targets)):
            raise ValueError(f'{self.id}: values must be integers within value_limit')

    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def load_puzzles(path):
    puzzles = {}
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'id', 'starting_values', 'targets', 'value_limit', 'registers'}
        if not required <= set(reader.fieldnames or []):
            raise ValueError(f'Missing puzzle columns: {sorted(required - set(reader.fieldnames or []))}')
        for row in reader:
            puzzle = Puzzle(row['id'], tuple(json.loads(row['starting_values'])),
                            tuple(json.loads(row['targets'])), int(row['value_limit']),
                            int(row['registers']))
            if puzzle.id in puzzles:
                raise ValueError(f'Duplicate puzzle ID: {puzzle.id}')
            puzzles[puzzle.id] = puzzle
    if not puzzles:
        raise ValueError('Puzzle CSV is empty')
    return puzzles


def encode_program(program):
    return json.dumps(program, separators=(',', ':'), ensure_ascii=True)


def require_scored_ids(ids):
    expected = {f'scored_{i:04d}' for i in range(1, 1001)}
    actual = set(ids)
    if actual != expected:
        raise ValueError(f'Competition requires exactly 1,000 scored IDs; '
                         f'missing={len(expected - actual)}, extra={len(actual - expected)}')


def write_submission(path, puzzles, programs, *, competition=False):
    from .validator import validate

    if set(puzzles) != set(programs):
        raise ValueError('Program IDs must match puzzle IDs exactly')
    if competition:
        require_scored_ids(puzzles)
    # Validate everything before opening the output; preserve an existing file on error.
    for puzzle_id, puzzle in puzzles.items():
        validate(puzzle, programs[puzzle_id])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', 'program'])
        for puzzle_id in sorted(puzzles):
            writer.writerow([puzzle_id, encode_program(programs[puzzle_id])])
    temporary.replace(path)
