import unittest
from tests.helpers import puzzle, TOY_PROGRAM
import csv
import tempfile
from pathlib import Path
from src.io import load_puzzles, write_submission
from src.score import score_submission
from src.validator import ValidationError
from src.cache import keep_best, load_best
from src.greedy import solve_one


class CacheTests(unittest.TestCase):
    def test_round_trip_and_cache(self):
        p = puzzle()
        program = solve_one(p)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'output.csv'
            write_submission(path, {p.id: p}, {p.id: program})
            scores, errors = score_submission({p.id: p}, path)
            self.assertEqual(errors, [])
            self.assertEqual(scores[p.id], len(program))
            keep_best(directory, p, program)
            longer = program + [['/', 0, 0, 47]]
            self.assertEqual(keep_best(directory, p, longer), program)
            self.assertEqual(load_best(directory, p), program)
            changed = puzzle(targets=(99,))
            self.assertIsNone(load_best(directory, changed))
