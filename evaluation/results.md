# Evaluation results

**Not yet measured.** Every cell below reads `—` until the prompt freeze
(Oct 22) and the 14 evaluation MRs have actually run. Nothing here is
predicted, estimated, or filled in advance.

A small controlled evaluation on one application. Not evidence of broad
superiority.

See [docs/evaluation-protocol.md](../docs/evaluation-protocol.md) for the
design, the freeze, and the adjudication rules.

| Metric | Definition | Baseline (Duo review + scans) | Baseline + Falsify |
| --- | --- | --- | --- |
| Defects found, tuned half | Seeded defects identified in the tuning half; scanner finds counted separately | — | — |
| Defects found, held-out half | Seeded defects identified in the held-out half, prompt and configuration frozen before | — | — |
| Precision | Defect claims corresponding to a real defect ÷ all defect claims. A struck wrong-spec experiment counts **against** Falsify | — | — |
| Recall | Seeded defects found ÷ 12; misses listed by ID | — | — |
| Unsupported functional findings | Functional defect claims with no reproducing test | — | **0 by construction** (reported, not compared) |
| Wrong-spec experiments struck | Red experiments the human ruled encoded the wrong spec | n/a | — |
| Experiments that failed to run | ERROR outcomes, and how many the one allowed rewrite rescued | n/a | — |
| Active human time per accepted finding | Minutes reading, ruling, applying, promoting ÷ accepted findings | — (review time per MR) | — |
| Total review wall time per MR | Reviewer assignment → merge-ready | — | — |
| Compute and token cost per MR | CI minutes + model tokens | — | — |
| Regression tests added | Experiments promoted into `tests/` across all MRs | **0** | — |
| Corroboration-only runs | MRs where Falsify found nothing and said so | n/a | — (target: the clean MR) |
| Prevented return | Seeded defects reintroduced in a follow-up change and caught by the promoted suite | n/a | — (target: all promoted) |

## Misses

Listed by ID once measured. A miss is as interesting as a find.

| ID | Condition | Why Falsify missed it |
| --- | --- | --- |
| — | | |

## Experiments struck

The strike count is part of the narrative, not a footnote.
"Falsify was wrong N times; here are the experiments I struck."

| ID | What it asserted | What the claim actually said | Ruled by |
| --- | --- | --- | --- |
| — | | | |

## Honest limitations

Written before the numbers, so they cannot be shaped by them.

1. **One application, one language.** Python, FastAPI, SQLite. Nothing here
   generalizes to a codebase of a different shape without being retested.
2. **Twelve seeded defects is a small sample.** A single find or miss moves
   recall by 8 percentage points.
3. **The author is the only human ruling.** Rulings are therefore consistent,
   and also unaudited by a second person. A team would surface wrong-spec
   experiments that a solo ruler agrees with.
4. **Concurrency is tested within one instance.** Production runs at max
   instances 1 with a SQLite file on the instance filesystem. Nothing here
   establishes distributed correctness.
5. **The seeded defects were written by the same person who wrote the
   Falsifier prompt.** The held-out half and the freeze are the mitigation,
   not a solution.
6. **A struck experiment is still a cost.** The human spent time reading a
   test that asserted the wrong thing. That time is counted in the human-time
   row, not excluded from it.
