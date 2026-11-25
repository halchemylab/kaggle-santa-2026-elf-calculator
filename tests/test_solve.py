import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.cache import load_best
from src.greedy import best_program
from src.io import Puzzle
from src.score import score_submission
from src.solve import main, worker
from src.solvers import SearchBudget, solve
from tests.helpers import puzzle


class SolveCLITests(unittest.TestCase):
    def test_legacy_worker_preserves_candidate_schedule(self):
        p = puzzle(targets=(123, 456, 789), limit=1000)
        _, _, program = worker((p, 1, 42, [4, 8], None, SearchBudget()))
        self.assertEqual(program, best_program(p, restarts=1, seed=42, bases=[4, 8]))

    def test_common_method_export_matches_benchmark_and_preserves_cache(self):
        puzzles = {
            f'practice_{i:04d}': Puzzle(f'practice_{i:04d}', (1009,), (target,), 10000)
            for i, target in enumerate((7063, 7066), 1)
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, report = (root / name for name in ('puzzles.csv', 'output.csv', 'report.json'))
            cache = root / 'cache'
            with source.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['id', 'starting_values', 'targets', 'value_limit', 'registers'])
                for p in puzzles.values():
                    writer.writerow([p.id, json.dumps(p.starting_values), json.dumps(p.targets),
                                     p.value_limit, p.registers])
            argv = ['solve', '--puzzles', str(source), '--output', str(output),
                    '--report', str(report), '--cache', str(cache), '--method', 'factor_offset',
                    '--candidates', '13', '--seed', '2027']
            with patch('sys.argv', argv), contextlib.redirect_stdout(io.StringIO()):
                main()
            scores, errors = score_submission(puzzles, output)
            self.assertEqual(errors, [])
            for p in puzzles.values():
                expected = solve(p, 'factor_offset', seed=2027, budget=SearchBudget(13)).program
                self.assertEqual(load_best(cache, p), expected)
                self.assertEqual(scores[p.id], len(expected))
            metadata = json.loads(report.read_text())
            self.assertEqual(metadata['method'], 'factor_offset')
            self.assertEqual(metadata['budget']['max_candidates'], 13)
            self.assertEqual(metadata['solver_interface'], 'common')
            # A later, worse binary run must still export the validated best cache.
            argv[argv.index('factor_offset')] = 'binary'
            with patch('sys.argv', argv), contextlib.redirect_stdout(io.StringIO()):
                main()
            self.assertEqual(score_submission(puzzles, output), (scores, []))

    def test_invalid_or_ambiguous_options_rejected(self):
        for options in (['--method', 'factor_offset', '--restarts', '2'],
                        ['--method', 'greedy', '--bases', '4'],
                        ['--candidates', '13'],
                        ['--method', 'factor_offset', '--candidates', '0'],
                        ['--competition']):
            with self.subTest(options=options), patch('sys.argv', ['solve', *options]), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
