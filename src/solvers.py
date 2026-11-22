"""Common solver interface, bounded experiments, and an arithmetic beam search."""

from dataclasses import dataclass, field
import math
import time

from .greedy import apply, solve_one
from .validator import validate

METHODS = ('binary', 'base_expansion', 'greedy', 'factor_offset', 'beam')


@dataclass(frozen=True)
class SearchBudget:
    # The fallback is always completed; time limits are checked between work units.
    max_candidates: int = 13
    seconds: float | None = None
    beam_width: int = 24
    beam_depth: int = 10
    beam_expansions: int = 250

    def __post_init__(self):
        if self.max_candidates < 1 or any(v < 1 for v in
                (self.beam_width, self.beam_depth, self.beam_expansions)):
            raise ValueError('Search budgets must be positive')
        if self.seconds is not None and (not math.isfinite(self.seconds) or self.seconds <= 0):
            raise ValueError('seconds must be positive')


@dataclass
class Solution:
    program: list
    candidates: int = 1
    expansions: int = 0
    budget_exhausted: bool = False
    notes: list[str] = field(default_factory=list)


def beam_search(puzzle, fallback, budget, expired):
    """Search primitive arithmetic instructions on tiny puzzles only.

    Keep generated values in free registers, with historical target coverage in
    each state. This first beam intentionally does not search register eviction.
    Every solution is replayed before it can replace the fallback.
    """
    if puzzle.value_limit > 512 or len(set(puzzle.targets)) > 6 or len(puzzle.starting_values) > 8:
        return fallback, 0, False, ['Beam skipped: tiny-puzzle limits exceeded; binary fallback used.']
    # State: defined register values, uncovered targets, instruction sequence.
    states = [(puzzle.starting_values, frozenset(puzzle.targets), ())]
    best, expansions = fallback, 0

    def rank(state):
        values, remaining, instructions = state
        # Coverage first; arithmetic distance breaks ties. This is a heuristic,
        # not an admissible lower bound or an optimality proof.
        distance = sum(min(abs(t - v).bit_length() for v in values) for t in remaining)
        return len(remaining), distance, len(instructions), values

    for _ in range(min(budget.beam_depth, len(best) - 1)):
        next_states = {}
        for values, remaining, instructions in states:
            if expansions >= budget.beam_expansions or expired():
                return best, expansions, True, []
            expansions += 1
            for a, x in enumerate(values):
                for b, y in enumerate(values):
                    for op in ('+', '-', '*', '/'):
                        if op in ('+', '*') and b < a:
                            continue
                        result = apply(op, x, y)
                        if result is None or not 1 <= result <= puzzle.value_limit:
                            continue
                        existing = next((i for i, v in enumerate(values) if v == result), None)
                        if existing is not None and result not in remaining:
                            continue
                        if existing is None and len(values) == puzzle.registers:
                            continue
                        destination = existing if existing is not None else len(values)
                        new_values = values if existing is not None else values + (result,)
                        new_remaining = remaining - {result}
                        new_instructions = instructions + ((op, a, b, destination),)
                        if not new_remaining:
                            candidate = [list(i) for i in new_instructions]
                            validate(puzzle, candidate)
                            if len(candidate) < len(best):
                                best = candidate
                            continue
                        if len(new_instructions) >= len(best) - 1:
                            continue
                        key = (tuple(sorted(set(new_values))), new_remaining)
                        next_states.setdefault(key, (new_values, new_remaining, new_instructions))
        if not next_states:
            return best, expansions, False, []
        states = sorted(next_states.values(), key=rank)[:budget.beam_width]
    return best, expansions, True, ['Beam depth reached; optimality is not established.']


def solve(puzzle, method, *, seed=2026, budget=None):
    """Return a fresh solution; never read the best-known cache."""
    if method not in METHODS:
        raise ValueError(f'Unknown solver: {method}')
    budget = budget or SearchBudget()
    started = time.perf_counter()
    expired = lambda: budget.seconds is not None and time.perf_counter() - started >= budget.seconds
    best = solve_one(puzzle, base=2, greedy=False)
    solution = Solution(best)
    if method == 'binary':
        return solution
    if method == 'beam':
        best, expanded, exhausted, notes = beam_search(puzzle, best, budget, expired)
        return Solution(best, expansions=expanded, budget_exhausted=exhausted, notes=notes)
    # Same base/order schedule isolates the immediate-target heuristic's effect.
    for attempt in range(budget.max_candidates - 1):
        if expired():
            solution.budget_exhausted = True
            break
        base = (4, 8, 16)[attempt % 3]
        cycle = attempt // 3
        order = ('ascending', 'descending')[cycle] if cycle < 2 else 'random'
        candidate = solve_one(puzzle, base=base, order=order,
                              seed=seed + cycle, greedy=method in ('greedy', 'factor_offset'),
                              factor_offset=method == 'factor_offset')
        validate(puzzle, candidate)
        solution.candidates += 1
        if len(candidate) < len(solution.program):
            solution.program = candidate
    validate(puzzle, solution.program)
    return solution
