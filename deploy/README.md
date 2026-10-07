# deploy/

Infrastructure as code for both Cloud Run environments. Nothing is created by
hand after `setup.sh` runs once.

| File | What it does |
| --- | --- |
| `setup.sh` | One-time: both services, Artifact Registry repo, WIF pool + provider + attribute condition |
| `cloudrun.staging.yaml` | Staging service. Scales to zero |
| `cloudrun.prod.yaml` | Production service. min instances 1, max instances 1 |
| `auth.sh` | Exchanges the GitLab OIDC ID token for a Google access token |
| `deploy.sh` | Deploys by image **digest**, never by tag |
| `rollback.sh` | Routes traffic to the previous revision |

## No stored cloud credentials

`deploy-*` jobs authenticate with GitLab's OIDC ID token, exchanged through
Workload Identity Federation. The WIF attribute condition requires:

- the project path, **and**
- the protected-environment claim

So a job on a scratch branch, on an MR branch, or in any other project gets no
cloud identity at all. This is Control 5 in `docs/controls.md`, and the
negative test is that the exchange is refused by Google — not by a conditional
in the pipeline.

## Why deploy by digest

The image tag is `<short-sha>-<certificate-hash>`, which ties every revision
to the certificate that let it merge. But the tag is mutable and the digest is
not, so `deploy.sh` deploys by digest and `events.md` records the digest.

`prod-watch` verifies the live revision's digest against `events.md` before it
samples anything. A mismatch is a hard failure, not a motion.

## Database

SQLite on the instance filesystem, with production at **max instances 1**.

Cloud Run's filesystem is instance-local and ephemeral, so the demo state is
disposable and reset by a job. The concurrency behaviour is therefore tested
**within one instance**, and the write-up says so rather than implying
distributed correctness. Cloud SQL only if time allows.

## Region

`us-east1`. Nearest to the author; irrelevant to judging.
