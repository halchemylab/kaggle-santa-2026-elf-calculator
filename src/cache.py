"""Fingerprint-aware best solutions. One coordinating process writes the cache."""

import json
from pathlib import Path
from .validator import validate


def cache_path(directory, puzzle):
    # Hash-based names avoid trusting IDs as filesystem paths.
    return Path(directory) / f'{puzzle.fingerprint()}.json'


def load_best(directory, puzzle):
    path = cache_path(directory, puzzle)
    if not path.exists():
        return None
    entry = json.loads(path.read_text(encoding='utf-8'))
    if entry['fingerprint'] != puzzle.fingerprint() or entry['id'] != puzzle.id:
        raise ValueError(f'{puzzle.id}: mismatched cache entry')
    validate(puzzle, entry['program'])
    return entry['program']


def keep_best(directory, puzzle, candidate):
    validate(puzzle, candidate)
    existing = load_best(directory, puzzle)
    if existing is not None and len(existing) <= len(candidate):
        return existing
    path = cache_path(directory, puzzle)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'id': puzzle.id, 'fingerprint': puzzle.fingerprint(),
                                     'program': candidate}), encoding='utf-8')
    temporary.replace(path)
    return candidate
