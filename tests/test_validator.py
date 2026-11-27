import unittest
from tests.helpers import puzzle, TOY_PROGRAM
from src.validator import ValidationError, validate


class ValidatorTests(unittest.TestCase):
    def test_toy(self):
        program = [['/', 0, 0, 1], ['-', 0, 1, 2], ['+', 0, 2, 3], ['+', 0, 3, 4]]
        self.assertEqual(validate(puzzle(), program), 4)

    def test_overwrite_reads_both_sources_first(self):
        self.assertEqual(validate(puzzle(targets=(6, 12)),
                                  [['+', 0, 0, 0], ['+', 0, 0, 0]]), 2)

    def test_coverage_survives_overwrite(self):
        self.assertEqual(validate(puzzle(targets=(1, 2)),
                                  [['/', 0, 0, 0], ['+', 0, 0, 0]]), 2)

    def test_initial_target_policy(self):
        p = puzzle(targets=(3,))
        with self.assertRaises(ValidationError):
            validate(p, [], initial_targets_count=False)
        self.assertEqual(validate(p, [], initial_targets_count=True), 0)
        self.assertEqual(validate(p, []), 0)
        self.assertEqual(validate(puzzle(starts=(3, 6), targets=(3, 12)),
                                  [['+', 1, 1, 0]]), 1)

    def test_illegal_instructions(self):
        cases = [
            [['+', 1, 0, 2]],  # undefined
            [['+', -1, 0, 2]], [['+', 0, 0, 48]],
            [['+', True, 0, 2]], [['+', 0.0, 0, 2]],
            [['-', 0, 0, 0]],  # zero cannot enter the calculator, including as divisor
            [['-', 0, 0, 1], ['/', 0, 1, 2]],
            [['/', 0, 0, 1], ['-', 1, 0, 2]],  # negative
            [['/', 0, 0, 1], ['+', 1, 1, 2], ['/', 0, 2, 3]],
            [['*', 0, 0, 0]] * 3,  # overflow
            [['^', 0, 0, 0]], [['+', 0, 0]], [[[], 0, 0, 0]],
        ]
        for program in cases:
            with self.subTest(program=program), self.assertRaises(ValidationError):
                validate(puzzle(targets=(1,)), program)

    def test_limits_and_malformed_json(self):
        for program in ('bad json', '{}', '[true]', ' ' * 131073 + '[]',
                        [['/', 0, 0, 1]] * 4097):
            with self.subTest(kind=type(program)), self.assertRaises(ValidationError):
                validate(puzzle(), program)

    def test_exact_large_integers(self):
        n = 998748313126407437
        p = puzzle(starts=(n,), targets=(n,), limit=n)
        self.assertEqual(validate(p, [['/', 0, 0, 1], ['*', 0, 1, 0]]), 2)

    def test_instructions_after_coverage_still_checked(self):
        with self.assertRaises(ValidationError):
            validate(puzzle(targets=(1,)), [['/', 0, 0, 1], ['-', 0, 0, 1]])
