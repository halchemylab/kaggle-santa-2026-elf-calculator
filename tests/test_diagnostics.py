import unittest

from benchmarks.diagnose_programs import inspect
from src.validator import validate
from tests.helpers import puzzle


class ProgramDiagnosticTests(unittest.TestCase):
    def test_pruning_preserves_historical_coverage_and_read_before_write(self):
        p = puzzle(starts=(3,), targets=(6, 7), limit=10)
        program = [['/', 0, 0, 1], ['+', 0, 0, 2],
                   ['+', 2, 1, 2], ['+', 0, 1, 3]]
        audit, pruned = inspect(p, program)
        self.assertEqual(pruned, program[:3])
        self.assertEqual(audit['removable_steps'], 1)
        self.assertEqual(validate(p, pruned), 3)

    def test_reconstruction_distinguishes_lost_values_from_resident_duplicates(self):
        p = puzzle(starts=(3,), targets=(6, 9), limit=10)
        program = [['+', 0, 0, 1], ['+', 1, 0, 1],
                   ['+', 0, 0, 2], ['+', 0, 0, 3]]
        audit, pruned = inspect(p, program)
        self.assertEqual(audit['evicted_value_reconstructions'], 1)
        self.assertEqual(audit['reconstruction_reasons'], {'source_overwritten': 1})
        self.assertEqual(audit['duplicate_results'], 1)
        self.assertEqual(pruned, program[:2])
