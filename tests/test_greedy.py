import unittest
from tests.helpers import puzzle, TOY_PROGRAM
import random
from src.greedy import best_program, solve_one
from src.validator import validate


class SolverTests(unittest.TestCase):
    def test_small_and_initial_targets(self):
        for limit in (1, 2, 3, 7, 31):
            p = puzzle(starts=(limit,), targets=tuple(range(1, limit + 1)), limit=limit)
            for base in (2, 4, 8, 16):
                for greedy in (False, True):
                    validate(p, solve_one(p, base=base, greedy=greedy))

    def test_eviction_and_large_targets(self):
        rng = random.Random(7)
        p = puzzle(targets=tuple(rng.sample(range(10**16, 10**18), 32)), limit=10**18)
        for base in (2, 4, 8, 16):
            validate(p, solve_one(p, base=base))

    def test_generated_small_puzzles(self):
        rng = random.Random(2026)
        for _ in range(40):
            limit = rng.randint(1, 10000)
            p = puzzle(starts=tuple(rng.randint(1, limit) for _ in range(rng.randint(1, 8))),
                       targets=tuple(rng.randint(1, limit) for _ in range(rng.randint(1, 10))),
                       limit=limit)
            validate(p, solve_one(p, base=8))

    def test_reproducible_and_no_regression_from_baseline(self):
        p = puzzle(targets=(123, 456, 789, 2048), limit=10000)
        a = best_program(p, restarts=1, seed=42)
        self.assertEqual(a, best_program(p, restarts=1, seed=42))
        self.assertLessEqual(len(a), len(solve_one(p, base=2, greedy=False)))
