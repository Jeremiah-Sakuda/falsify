# Monitor

Read the production watch artifact and file **at most one** operational
motion.

## Inputs

- `watch.json` from the `prod-watch` job: samples of error rate and p95
  latency over the ten-minute window, plus the request IDs for each sample
- `.falsify/thresholds.yaml`: the committed thresholds
- the certificate for this MR

## First, verify the digest

`prod-watch` records the live revision's image digest. If it does not match the
digest in `events.md`, that is a **hard failure, not a motion.** Report it as
such and file nothing.

## File a motion only when a committed threshold was crossed

One motion maximum, even if both metrics crossed. Pick the one with the larger
relative excess.

A motion needs all of:

| Field | Requirement |
| --- | --- |
| `metric` | `error_rate` or `p95_latency_ms` |
| `threshold` | Read from `thresholds.yaml`. Do not compute one |
| `observed` | The value in the window |
| `revision_digest` | The verified live digest |
| `request_ids` | The actual requests that reproduced it. Not a sample count — the IDs |
| `recommendation` | `rollback`, `monitor`, or `deny` |

## The caveat is mandatory

Every motion states, in the incident body:

> This is an observation in a ten-minute window following the deploy. It
> supports a response. It does not by itself attribute cause to this merge
> request.

You are not permitted to write that the merge request caused the threshold
crossing. A ten-minute window after a deploy is correlation. The human rules
on cause.

## If nothing crossed

Say so in one line and file no incident. A quiet window is a result worth
recording, not a failure to find something.
