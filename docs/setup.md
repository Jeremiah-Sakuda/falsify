# Setup

## Local development

The app targets **Python 3.12**. Newer interpreters will likely work for local
poking, but CI and the container pin 3.12, so develop against it.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Run the base suite:

```bash
pytest tests/ -v
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000> for the landing page, or
<http://127.0.0.1:8000/docs> for the API docs.

Seed some data:

```bash
python -m scripts.seed
```

## Running an experiment harness locally

The harness that CI uses is the same script, so you can reproduce a refutation
without a pipeline:

```bash
python -m scripts.run_experiments \
  --experiments .falsify/experiments \
  --head HEAD \
  --base main \
  --out experiments.json
```

It prints the classification table and writes `experiments.json` in the same
shape the `experiments` CI job produces.

## GitLab project configuration

Settings that must be set by hand once, because they are project settings
rather than repository files.

### Required

| Setting | Value | Why |
| --- | --- | --- |
| Duo Agent Platform | Enabled | Custom flows |
| Custom flows and triggers | Enabled for the group | Day-one blocker — confirm before writing YAML |
| Protected branch `main` | Maintainers merge, no force push | Keeps service accounts off main |
| Protected environments `staging`, `production` | Maintainers only; `production` requires deployment approval | Gate 4; also the WIF condition |
| Approval rule | ≥1 human approval, service accounts excluded as eligible approvers | Agents cannot approve themselves |
| Required pipeline success | On | The `certificate` job is the merge gate |
| Security scanning | SAST, dependency scanning, secret detection | Secure stage |
| Audit events | On | Gate 4 approvals, flag toggles, incident actions |
| Feature flags | On, Unleash client configured | Configure stage |

### Service accounts

One per flow, Developer role:

| Account | Flow | Trigger |
| --- | --- | --- |
| `ai-plan-gitlab-duo` | `plan.yaml` | mention |
| `ai-trial-gitlab-duo` | `trial.yaml` | assign reviewer |
| `ai-monitor-gitlab-duo` | `monitor.yaml` | mention |

Developer permits pushes to any unprotected branch, which is why the
scratch-branch restriction is enforced in three layers rather than by role.
See [controls.md](controls.md) Control 2.

### Solo-owner relaxations

Two defaults are relaxed for a single builder, and this is stated in the
README rather than buried:

- MR authors may approve their own MRs
- The person who ran a deployment pipeline may approve its deployment

The separation of duties in that configuration is between the agent and the
human, not between two humans.

### CI/CD variables

By design, almost nothing. No cloud credentials — `deploy-*` jobs use OIDC.

| Variable | Scope | Protected | Purpose |
| --- | --- | --- | --- |
| `FALSIFY_PROMOTE_TOKEN` | project | yes | Project access token for the `promote` job's push (a `CI_JOB_TOKEN` push would not start a pipeline) |
| `GCP_PROJECT_ID` | project | no | Not a secret |
| `GCP_WIF_PROVIDER` | project | yes | WIF provider resource name |
| `GCP_DEPLOY_SA` | project | yes | Service account to impersonate |
| `UNLEASH_INSTANCE_ID` | project | yes | Feature flag client |
| `UNLEASH_APP_NAME` | project | no | Feature flag client |

## Google Cloud setup

One-time, from `deploy/`:

```bash
cd deploy
./setup.sh
```

It creates both Cloud Run services, the Artifact Registry repository, the
Workload Identity pool and provider, and the attribute condition that binds
deploy identity to this project path and the protected-environment claim.

Nothing is created by hand after that. See [deploy/README.md](../deploy/README.md).
