# Santa 2026 — The Elf Calculator

Source: competition overview and evaluation pasted by the user on November 21,
2026. Official competition: https://www.kaggle.com/competitions/santa-2026
Data rules: https://www.kaggle.com/competitions/santa-2026/data
The user supplied the official Data page text on November 27, 2026, confirming
initialization and target coverage. The scored puzzles and sample are now local.

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

## Initialization and coverage confirmed from the Data page

1. `starting_values` initialize consecutive registers beginning at register 0;
   every other register starts undefined.
2. Targets are covered when their values appear in any register, including at
   the start. Coverage survives overwrites. Validator and solvers now use this
   rule by default. `initial_targets_count=False` remains available in the
   validator for historical replay. An empty program is valid if all targets
   are present initially; instructions after coverage must still be legal.
3. `lower_bound`, `family`, and `design_tier` are practice metadata, not mandatory
   inputs to the solver. `lower_bound` is the number of distinct targets absent
   from starting_values. It is generally loose and need not be achievable.

The official sample was independently replayed on November 27: all 1,000
programs validate, totaling 1,490,379 instructions, with a maximum of 2,873.
The old conservative coverage policy rejected three sample rows solely because
initially present targets were not reproduced. The user subsequently submitted
`scored_first.csv`; Kaggle accepted it with score 392,980, exactly matching local
validation. This result was reported by the user on November 27.

Benchmarks before this confirmation required explicit production of initial
targets. New reports record `initial_targets_count: true`; reports lacking the
field used the historical policy. The dashboard blocks cross-policy comparisons.

## Dates supplied by the user

Start: November 18, 2026. Entry and team merger deadline: January 21, 2027.
Final submission deadline: January 28, 2027. Deadlines are 23:59 UTC unless updated
by the organizers. Check Kaggle for current rules and timeline before submitting.

Citation supplied by the user: Walter Reade and María Cruz. Santa 2026 - The Elf
Calculator. Kaggle, 2026.
