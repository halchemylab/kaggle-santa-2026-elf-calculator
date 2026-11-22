# Santa 2026 — The Elf Calculator

Source: competition overview and evaluation pasted by the user on November 21,
2026. Official competition: https://www.kaggle.com/competitions/santa-2026
Data rules: https://www.kaggle.com/competitions/santa-2026/data
The Data page could not be retrieved during setup; the notes below are not a
substitute for its initialization and target-coverage definitions.

## Calculator and scoring

Produce every target at least once with positive integer arithmetic. The score is
the total instructions across 1,000 puzzles; lower is better. No partial credit:
one invalid program rejects the submission. There is no public/private split.

An instruction is `[operator, source_a, source_b, destination]`. Operators are
`+`, `-`, `*`, `/`. Register indices are integers 0 through 47. Both sources must
be defined; they are read before the destination is overwritten. Sources may be
identical, and the destination may equal either source. Division must be exact.
Every result must be a positive integer no larger than that puzzle's value_limit.
Do not use floating-point arithmetic.

Limits per puzzle: 48 registers, 4,096 instructions, and 131,072 UTF-8 bytes in
the program cell. All instructions count, including duplicates and instructions
after coverage. The pasted upper bound on value_limit was missing its formula;
use the exact bound in each CSV row rather than guessing a global bound.

## Submission

UTF-8 CSV, exactly `id,program` in that order. Each ID from `scored_0001` through
`scored_1000` exactly once. Each program is a JSON array of four-element arrays.
Use a CSV writer to escape JSON quotes. Row order does not matter.

Toy example: initial register 0 holds 3, targets are 1, 2, 5, 8:
`[["/",0,0,1],["-",0,1,2],["+",0,2,3],["+",0,3,4]]`.
Its illustrative ID must not appear in a competition submission.

## Assumptions requiring the Data page or official replay code

1. `starting_values` initialize consecutive registers beginning at register 0;
   every other register starts undefined.
2. Whether initial values count toward target coverage is unspecified in the
   pasted overview. This repository conservatively requires an instruction to
   produce each target, even if initially present. This may cost extra instructions
   but ensures coverage under either interpretation. The simulator has an explicit
   `initial_targets_count` option for testing after the official rule is confirmed.
3. `lower_bound`, `family`, and `design_tier` are practice metadata, not mandatory
   inputs to the solver. Do not treat a lower bound as an achieved solution.

The official sample is said to use at most 2,873 instructions in any program.
That claim and its total score have not been checked locally because the file
has not been provided. Do not infer leaderboard competitiveness from this maximum.

## Dates supplied by the user

Start: November 18, 2026. Entry and team merger deadline: January 21, 2027.
Final submission deadline: January 28, 2027. Deadlines are 23:59 UTC unless updated
by the organizers. Check Kaggle for current rules and timeline before submitting.

Citation supplied by the user: Walter Reade and María Cruz. Santa 2026 - The Elf
Calculator. Kaggle, 2026.
