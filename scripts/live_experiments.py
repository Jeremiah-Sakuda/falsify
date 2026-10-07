#!/usr/bin/env python3
"""NOT YET IMPLEMENTED — referenced by .gitlab-ci.yml.

See scripts/README.md for which scripts are implemented and which are not.
This stub exits non-zero rather than silently succeeding: a govern or monitor
job that cannot do its work must fail the pipeline, not pass it.
"""
import sys

PURPOSE = {
    "gitlab_state": (
        "Fetch Gate 1 / Gate 2 / Gate 3 state and promotion records from the "
        "GitLab API into state.json for the certificate job. Build block 4."
    ),
    "certificate_verify": (
        "On main: fetch the merged MR's certificate artifact, confirm the "
        "merge commit's tree matches the certified head (or a documented "
        "merge of it), and that every promoted file is present with its "
        "recorded hash. Build block 4."
    ),
    "live_experiments": (
        "Replay the conjectures as HTTP against the staging host only — its "
        "one permitted destination — once per feature flag state, at the rate "
        "in .falsify/thresholds.yaml. Build block 6."
    ),
    "prod_watch": (
        "Verify the live revision's image digest against events.md, then "
        "sample error rate and p95 latency for the committed window while "
        "replaying the conjectures at production-like rate. Build block 6."
    ),
}

print(f"scripts/live_experiments.py is not implemented yet.", file=sys.stderr)
print(f"Intended behaviour: {PURPOSE['live_experiments']}", file=sys.stderr)
sys.exit(2)
