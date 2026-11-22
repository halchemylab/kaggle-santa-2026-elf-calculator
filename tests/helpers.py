from src.io import Puzzle


def puzzle(starts=(3,), targets=(1, 2, 5, 8), limit=100):
    return Puzzle('example_0001', starts, targets, limit)


TOY_PROGRAM = [['/', 0, 0, 1], ['-', 0, 1, 2], ['+', 0, 2, 3], ['+', 0, 3, 4]]
