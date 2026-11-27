import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.benchmark import (comparisons, dataset_fingerprint, evaluate, make_split,
                           run_benchmark, seed_statistics, select_split, summarize)
from src.dashboard import build_dashboard
from src.io import Puzzle
from src.score import score_submission
from src.solvers import SearchBudget, Solution, solve
from src.validator import validate
from tests.helpers import puzzle


class SolverInterfaceTests(unittest.TestCase):
    def test_methods_return_valid_fresh_solutions(self):
        p = puzzle(targets=(2, 5), limit=8)
        baseline = solve(p, 'binary')
        for method in ('binary', 'base_expansion', 'greedy', 'factor_offset', 'factor_prefix', 'beam'):
            result = solve(p, method, budget=SearchBudget(max_candidates=7))
            validate(p, result.program)
            self.assertLessEqual(len(result.program), len(baseline.program))

    def test_beam_finds_shorter_small_program(self):
        p = puzzle(targets=(2, 5), limit=8)
        result = solve(p, 'beam')
        self.assertEqual(len(result.program), 3)
        self.assertLess(len(result.program), len(solve(p, 'binary').program))
        self.assertGreater(result.expansions, 0)

    def test_beam_large_puzzle_uses_valid_fallback(self):
        p = puzzle(targets=(10**17,), limit=10**18)
        result = solve(p, 'beam')
        self.assertEqual(result.program, solve(p, 'binary').program)
        self.assertIn('skipped', result.notes[0])

    def test_expired_budget_preserves_fallback(self):
        p = puzzle()
        result = solve(p, 'greedy', budget=SearchBudget(seconds=1e-12))
        self.assertTrue(result.budget_exhausted)
        self.assertEqual(result.program, solve(p, 'binary').program)

    def test_repeated_seed_is_reproducible(self):
        p = puzzle(targets=(123, 456, 789), limit=10000)
        for method in ('greedy', 'factor_offset', 'factor_prefix'):
            a = solve(p, method, seed=42)
            self.assertEqual(a.program, solve(p, method, seed=42).program)

    def test_invalid_budgets_rejected(self):
        for settings in ({'seconds': float('nan')}, {'seconds': 0}, {'seconds': float('inf')},
                         {'max_candidates': 0}, {'beam_width': 0}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                SearchBudget(**settings)

    def test_invalid_solver_result_is_rejected_independently(self):
        with patch('src.benchmark.solve', return_value=Solution([])):
            row, program = evaluate((puzzle(), 'greedy', 1, SearchBudget()))
        self.assertFalse(row['valid'])
        self.assertIsNone(row['steps'])
        self.assertIsNone(program)
        self.assertIn('targets missing', row['error'])


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.puzzles = {f'p_{i}': Puzzle(f'p_{i}', (3,), (2, i + 5), 100) for i in range(10)}

    def test_frozen_split_disjoint_complete_and_order_independent(self):
        manifest = make_split(self.puzzles)
        self.assertEqual(manifest, make_split(dict(reversed(list(self.puzzles.items())))))
        self.assertEqual(len(manifest['holdout']), 2)
        self.assertFalse(set(manifest['train']) & set(manifest['holdout']))
        self.assertEqual(len(select_split(self.puzzles, manifest, 'all')), 10)
        altered = dict(self.puzzles)
        altered['p_0'] = Puzzle('p_0', (3,), (99,), 100)
        with self.assertRaises(ValueError):
            select_split(altered, manifest, 'train')

    def test_fingerprint_includes_puzzle_contents(self):
        original = dataset_fingerprint(self.puzzles)
        self.puzzles['p_0'] = Puzzle('p_0', (3,), (98,), 100)
        self.assertNotEqual(original, dataset_fingerprint(self.puzzles))

    def test_run_artifacts_validate_and_dashboard_escapes_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / 'run-one'
            report = run_benchmark(self.puzzles, methods=['binary', 'greedy'], seeds=[42],
                budget=SearchBudget(max_candidates=4), run_dir=run_dir,
                metadata={'label': '</script><script>alert(1)</script>'})
            self.assertEqual(len(report['results']), 20)
            self.assertTrue(report['portfolio']['complete'])
            for path in report['program_files'].values():
                _, errors = score_submission(self.puzzles, run_dir / path)
                self.assertFalse(errors)
            dashboard = build_dashboard(directory)
            html = dashboard.read_text(encoding='utf-8')
            self.assertNotIn('__BENCHMARK_DATA__', html)
            self.assertNotIn('</script><script>alert(1)</script>', html)
            self.assertIn('\\u003c/script\\u003e', html)
            with self.assertRaises(FileExistsError):
                run_benchmark(self.puzzles, methods=['binary'], seeds=[1],
                              budget=SearchBudget(), run_dir=run_dir)

    def test_failed_programs_never_update_cache_or_export(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('src.benchmark.solve', return_value=Solution([])), \
                    patch('src.benchmark.keep_best') as keep:
                report = run_benchmark(self.puzzles, methods=['greedy'], seeds=[1],
                    budget=SearchBudget(), run_dir=Path(directory) / 'invalid', update_cache='unused')
            keep.assert_not_called()
            self.assertIsNone(report['summaries'][0]['total_steps'])
            self.assertIsNone(report['portfolio']['total_steps'])
            self.assertEqual(report['program_files'], {})

    def test_partial_totals_not_misrepresented_as_complete(self):
        rows = [{'method': 'x', 'seed': 1, 'puzzle_id': 'a', 'valid': True,
                 'steps': 5, 'seconds': 1}]
        summaries, portfolio = summarize(rows, ['a', 'b'])
        self.assertIsNone(summaries[0]['total_steps'])
        self.assertIsNone(portfolio['total_steps'])

    def test_comparison_direction_and_seed_statistics(self):
        rows = [{'method': m, 'seed': 1, 'puzzle_id': p, 'valid': True,
                 'steps': n, 'seconds': 1} for m, p, n in
                [('binary', 'a', 10), ('binary', 'b', 10),
                 ('greedy', 'a', 8), ('greedy', 'b', 13)]]
        comparison = comparisons(rows)[0]
        self.assertEqual((comparison['wins'], comparison['losses'], comparison['steps_saved']), (1, 1, -1))
        self.assertEqual(comparison['largest_regressions'][0], ('b', -3))
        summaries, _ = summarize(rows, ['a', 'b'])
        stats = seed_statistics(summaries)
        self.assertEqual(stats[0]['mean_steps'], 20)
        self.assertEqual(stats[1]['mean_steps'], 21)

    def test_empty_dashboard(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(build_dashboard(directory).exists())


if __name__ == '__main__':
    unittest.main()
