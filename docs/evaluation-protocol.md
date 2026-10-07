# Evaluation protocol

The impact criterion asks whether the solution addresses the problem "based on
what's demonstrated," so the submission carries a **measured comparison**
rather than a claim.

Described everywhere as a small controlled evaluation on one application, not
evidence of broad superiority.

## Design

Two conditions over the same 14 MRs (12 seeded, 2 unseeded):

| Condition | What runs |
| --- | --- |
| **Baseline** | GitLab Duo Code Review + the same security scans |
| **Treatment** | That baseline **plus** Falsify |

The comparison is between *equivalent workflows*. The question the table
answers is: **what does adding Falsify catch or resolve that the baseline
workflow does not, and at what human cost?**

Scanner-originated findings are counted **separately** from agent-generated
experimental findings in both conditions, so Falsify is never credited for
what the scanner found.

Both conditions run from the **same starting state per MR**, so tests promoted
on earlier MRs do not advantage later measurements.

## The freeze

The comparison runs once the Falsifier prompt is frozen — **end of week two,
Oct 22.** The freeze is recorded in the repo as a tagged commit.

The freeze covers:
- the Falsifier and Advocate prompts
- the model and configuration
- the experiment harness
- the thresholds
- the procedure

Tuning touches the first six seeded defects only. The held-out six and the two
unseeded MRs are **first run after the freeze**, and the two halves are
reported separately.

## Where the answer key lives

Seed descriptions, reference fixes, and evaluation metadata live **outside the
repository and outside any agent's reachable context** — in untracked
`planning/corpus.md`. The Falsifier reads this repository; a committed corpus
would void the held-out half.

`docs/PRD.md` §12 is redacted to a pointer for the same reason.

## Adjudication

A real bug found **outside** the seeded set counts as a true positive only if
a reference fix is written and the experiment passes against it.

A struck wrong-spec experiment **counts against** Falsify in the precision
figure. It is reported, not hidden.

## Metrics

See [evaluation/results.md](../evaluation/results.md) for the table that gets
filled from real runs.

## Honest framing

The write-up says three things together:

1. Falsify cannot make an unsupported functional claim.
2. Falsify can still be wrong about the spec.
3. Here is the strike count.

"Falsify was wrong N times; here are the experiments I struck" is part of the
narrative, not a footnote.

Falsify is presented as a **complement** to Duo Code Review throughout: Duo
reads and comments, Falsify runs experiments, and the two together are the
pitch to a GitLab judge.
