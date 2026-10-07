# evaluation/

The measured comparison. `results.md` is the table; it stays at `—` until the
runs happen.

## What is NOT here

Seed descriptions, reference fixes, and evaluation metadata live **outside
this repository** — in untracked `planning/corpus.md`.

The Falsifier reads this repository. A committed answer key would void the
held-out half of the evaluation, which is the only part of it that is worth
anything.

`docs/PRD.md` §12 is redacted to a pointer for the same reason.

## Procedure

1. Run both conditions on each of the 14 MRs from the same starting state.
2. Record raw numbers in untracked `planning/measurements/`.
3. Summarize into `results.md` only once a metric is complete.
4. Count scanner-originated findings separately from agent-generated
   experimental findings, in both conditions.

## The freeze

Tagged commit, end of week two (Oct 22). Covers the Falsifier and Advocate
prompts, the model and configuration, the experiment harness, the thresholds,
and the procedure.

The held-out half and the two unseeded MRs run for the first time **after**
the tag.
