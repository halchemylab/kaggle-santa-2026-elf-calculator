"""Export validated best-known cache programs; refuse missing or invalid entries."""

import argparse
from .cache import load_best
from .io import load_puzzles, write_submission


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--puzzles', required=True)
    parser.add_argument('--cache', default='cache/best')
    parser.add_argument('--output', required=True)
    parser.add_argument('--competition', action='store_true')
    args = parser.parse_args()
    puzzles = load_puzzles(args.puzzles)
    programs = {key: load_best(args.cache, puzzle) for key, puzzle in puzzles.items()}
    missing = [key for key, program in programs.items() if program is None]
    if missing:
        raise ValueError(f'Missing {len(missing)} cached programs; first: {missing[0]}')
    write_submission(args.output, puzzles, programs, competition=args.competition)
    print(f'Validated {len(programs)} programs; total {sum(map(len, programs.values()))}')


if __name__ == '__main__':
    main()
