"""Control 1 probe: the experiment child process must carry no job token.

Run by the `controls` job, not by `experiments`. This probe PASSES when the
credential is absent — i.e. when the control is working.
"""
import os

SENSITIVE = (
    "CI_JOB_TOKEN",
    "CI_REGISTRY_PASSWORD",
    "CI_DEPLOY_PASSWORD",
    "FALSIFY_PROMOTE_TOKEN",
    "GCP_WIF_PROVIDER",
    "GCP_DEPLOY_SA",
    "GITLAB_TOKEN",
)


def test_no_credentials_reach_experiment_code():
    leaked = [name for name in SENSITIVE if os.environ.get(name)]
    assert not leaked, (
        f"Control 1 FAILED OPEN: these credentials reached experiment code: {leaked}. "
        "The experiments job must execute pytest in a child process started with a "
        "scrubbed environment (env -i plus only what conftest needs)."
    )


def test_environment_is_actually_scrubbed():
    # A scrubbed env should be small. A full GitLab job env is ~100+ vars.
    assert len(os.environ) < 25, (
        f"Control 1 SUSPECT: {len(os.environ)} environment variables visible. "
        f"Expected a scrubbed child environment. Saw: {sorted(os.environ)}"
    )
