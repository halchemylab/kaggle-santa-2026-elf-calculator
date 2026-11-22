"""Greedy shared-register arithmetic with a bounded base-expansion fallback.

Try an immediate remaining target before constructing the next target. Otherwise
reuse an existing base-expansion prefix and retain results in an LRU register
cache. No unbounded exploratory intermediates can consume the instruction budget.
"""

import random
from .validator import validate


def apply(op, a, b):
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    if op == '*':
        return a * b
    return a // b if b and a % b == 0 else None


def solve_one(puzzle, *, base=8, order='ascending', seed=0, greedy=True,
              factor_offset=False):
    if base not in (2, 4, 8, 16):
        raise ValueError('base must be 2, 4, 8, or 16')
    if order not in ('ascending', 'descending', 'random'):
        raise ValueError('Unknown target order')
    base = min(base, puzzle.value_limit)
    values = [None] * puzzle.registers
    values[:len(puzzle.starting_values)] = puzzle.starting_values
    program, protected, touched = [], set(), [0] * puzzle.registers
    remaining = set(puzzle.targets)

    def lookup(value):
        return next((i for i, v in enumerate(values) if v == value), None)

    def allocate():
        available = [i for i in range(puzzle.registers) if i not in protected]
        empty = next((i for i in available if values[i] is None), None)
        return empty if empty is not None else min(available, key=lambda i: touched[i])

    def emit(op, a, b, destination):
        result = apply(op, values[a], values[b])
        if result is None or not 1 <= result <= puzzle.value_limit:
            raise ValueError('Solver attempted an illegal operation')
        program.append([op, a, b, destination])
        values[destination] = result
        for i in (a, b, destination):
            touched[i] = len(program)
        remaining.discard(result)

    # Save 1 permanently. Initial targets still require an emitted instruction.
    one = lookup(1)
    if one is None:
        one = allocate()
        emit('/', 0, 0, one)
    protected.add(one)
    constants = {1: one}
    # Positive digits and the multiplier. Limit 1 needs no base expansion.
    for digit in range(2, base + 1):
        register = lookup(digit)
        if register is None:
            register = allocate()
            emit('+', constants[digit - 1], one, register)
        constants[digit] = register
        protected.add(register)

    targets = sorted(remaining, reverse=order == 'descending')
    if order == 'random':
        random.Random(seed).shuffle(targets)

    def immediate():
        # Enumerate once per target construction; source values are read before dst.
        defined = [(i, value) for i, value in enumerate(values) if value is not None]
        for a, x in defined:
            for b, y in defined:
                for op in ('+', '-', '*', '/'):
                    result = apply(op, x, y)
                    if result in remaining:
                        return op, a, b
        return None

    def construct(target):
        # Reuse the longest stored prefix, keeping all partial values <= target.
        digits, prefix = [], target
        source = lookup(prefix)
        while source is None:
            prefix, digit = divmod(prefix, base)
            digits.append(digit)
            source = lookup(prefix)
        if not digits:
            return source
        destination = allocate()
        for digit in reversed(digits):
            emit('*', source, constants[base], destination)
            if digit:
                emit('+', destination, constants[digit], destination)
            source = destination
        return source

    def short_plan(target):
        """Compare bounded factor/offset plans with plain base construction.

        Construct just one quotient or difference by base expansion. Factors are
        retained values; signed offsets are existing constants 1 through base.
        No recursive factor search or trial division of large numbers is used.
        """
        stored = {v: i for i, v in enumerate(values) if v is not None}
        costs = {}

        def cost(value):
            if value not in costs:
                prefix, steps = value, 0
                while prefix not in stored:
                    prefix, digit = divmod(prefix, base)
                    steps += 1 + bool(digit)
                costs[value] = steps
            return costs[value]

        best_cost, best = cost(target), None
        offsets = [0] + [sign * d for d in constants for sign in (1, -1)]
        for value, register in stored.items():
            # Nearby retained values: target = value +/- constructed difference.
            difference = abs(target - value)
            if 0 < difference < target:
                steps = cost(difference) + 1
                if steps < best_cost:
                    best_cost = steps
                    best = (difference, '+' if target > value else '-', register, 0)
            if value <= 1:
                continue
            for offset in offsets:
                product = target - offset
                if not 1 <= product <= puzzle.value_limit:
                    continue
                quotient, remainder = divmod(product, value)
                if remainder or not 1 <= quotient < target:
                    continue
                steps = cost(quotient) + 1 + bool(offset)
                if steps < best_cost:
                    best_cost = steps
                    best = (quotient, '*', register, offset)
        return best

    while remaining:
        if greedy:
            direct = immediate()
            if direct:
                emit(*direct, allocate())
                continue
        target = next(t for t in targets if t in remaining)
        existing = lookup(target)
        if existing is not None:
            emit('*', existing, one, allocate())
            continue
        plan = short_plan(target) if factor_offset else None
        if plan is None:
            construct(target)
            continue
        value, op, retained, offset = plan
        # Preserve operands needed after constructing the quotient/difference,
        # even when every register is occupied and allocation must evict a value.
        was_protected = retained in protected
        protected.add(retained)
        source = construct(value)
        emit(op, retained, source, destination := allocate())
        if offset:
            emit('+' if offset > 0 else '-', destination,
                 constants[abs(offset)], destination)
        if not was_protected:
            protected.remove(retained)
    validate(puzzle, program)
    return program


def best_program(puzzle, *, restarts=2, seed=0, bases=(4, 8, 16)):
    if restarts < 0:
        raise ValueError('restarts must be nonnegative')
    # Always compare a simple deterministic binary baseline to every greedy candidate.
    best = solve_one(puzzle, base=2, greedy=False)
    for base in bases:
        for attempt in range(restarts + 2):
            order = ('ascending', 'descending')[attempt] if attempt < 2 else 'random'
            candidate = solve_one(puzzle, base=base, order=order, seed=seed + attempt)
            if len(candidate) < len(best):
                best = candidate
    validate(puzzle, best)
    return best
