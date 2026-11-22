"""Independent exact replay of all calculator instructions."""

import json
from .io import encode_program

MAX_STEPS = 4096
MAX_BYTES = 131072


class ValidationError(ValueError):
    pass


def validate(puzzle, program, *, initial_targets_count=False):
    """Return instruction count; raise ValidationError with the failing step.

    Starts are placed in consecutive registers from zero. Until confirmed against
    official Data rules, require initial targets to be produced by an instruction.
    For raw JSON cells, byte limits apply to the original text, including spaces.
    """
    if isinstance(program, str):
        raw = program
        try:
            program = json.loads(raw)
        except (ValueError, RecursionError) as error:
            raise ValidationError(f'Invalid program JSON: {error}') from error
    else:
        try:
            raw = encode_program(program)
        except (TypeError, ValueError, RecursionError) as error:
            raise ValidationError(f'Program is not JSON serializable: {error}') from error
    if len(raw.encode('utf-8')) > MAX_BYTES:
        raise ValidationError('Program exceeds 131,072 UTF-8 bytes')
    if not isinstance(program, list) or len(program) > MAX_STEPS:
        raise ValidationError('Program must be an array with at most 4,096 instructions')
    registers = [None] * puzzle.registers
    registers[:len(puzzle.starting_values)] = puzzle.starting_values
    remaining = set(puzzle.targets)
    if initial_targets_count:
        remaining.difference_update(puzzle.starting_values)
    for step, instruction in enumerate(program):
        def fail(message):
            raise ValidationError(f'{puzzle.id}, instruction {step}: {message}')

        if not isinstance(instruction, list) or len(instruction) != 4:
            fail('Expected [operator, source_a, source_b, destination]')
        op, a, b, destination = instruction
        if not isinstance(op, str) or op not in ('+', '-', '*', '/'):
            fail('Unknown operator')
        if any(type(index) is not int or not 0 <= index < puzzle.registers
               for index in (a, b, destination)):
            fail('Register indices must be integers from 0 through 47')
        x, y = registers[a], registers[b]
        if x is None or y is None:
            fail('Undefined source register')
        if op == '+':
            result = x + y
        elif op == '-':
            result = x - y
        elif op == '*':
            result = x * y
        else:
            if y == 0 or x % y:
                fail('Division must be nonzero and exact')
            result = x // y
        if not 1 <= result <= puzzle.value_limit:
            fail('Result must be positive and no greater than value_limit')
        registers[destination] = result
        remaining.discard(result)
    if remaining:
        raise ValidationError(f'{puzzle.id}: {len(remaining)} targets missing; '
                              f'first={min(remaining)}')
    return len(program)
