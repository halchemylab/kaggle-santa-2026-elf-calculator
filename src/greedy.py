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


def solve_one(puzzle, *, base=8, order='ascending', seed=0, greedy=True):
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
        # Find the longest already stored base prefix; every partial result <= target.
        digits, prefix = [], target
        source = lookup(prefix)
        while source is None:
            prefix, digit = divmod(prefix, base)
            digits.append(digit)
            source = lookup(prefix)
        destination = allocate()
        for digit in reversed(digits):
            emit('*', source, constants[base], destination)
            if digit:
                emit('+', destination, constants[digit], destination)
            source = destination
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
