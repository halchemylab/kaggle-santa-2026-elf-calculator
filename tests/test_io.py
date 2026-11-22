import unittest
from tests.helpers import puzzle, TOY_PROGRAM
import csv
import tempfile
from pathlib import Path
from src.io import load_puzzles, write_submission
from src.score import score_submission
from src.validator import ValidationError


class IOTests(unittest.TestCase):
    def test_csv_round_trip(self):
        p = puzzle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'output.csv'
            write_submission(path, {p.id: p}, {p.id: TOY_PROGRAM})
            scores, errors = score_submission({p.id: p}, path)
            self.assertEqual(errors, [])
            self.assertEqual(scores[p.id], len(TOY_PROGRAM))

    def test_missing_duplicate_unknown_ids(self):
        p = puzzle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.csv'
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['id', 'program'])
                writer.writerow(['unknown', '[]'])
                writer.writerow(['unknown', '[]'])
            _, errors = score_submission({p.id: p}, path)
            self.assertEqual(len(errors), 3)

    def test_refuse_invalid_export_and_practice_competition(self):
        p = puzzle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'output.csv'
            with self.assertRaises(ValidationError):
                write_submission(path, {p.id: p}, {p.id: []})
            self.assertFalse(path.exists())
            with self.assertRaises(ValueError):
                write_submission(path, {p.id: p}, {p.id: TOY_PROGRAM}, competition=True)

    def test_official_sample_when_available(self):
        data = Path('data')
        puzzles_path = data / 'scored_puzzles.csv'
        sample_path = data / 'sample_submission.csv'
        if not puzzles_path.exists() or not sample_path.exists():
            self.skipTest('Download scored_puzzles.csv and sample_submission.csv into data/')
        _, errors = score_submission(load_puzzles(puzzles_path), sample_path, competition=True)
        self.assertEqual(errors, [])
