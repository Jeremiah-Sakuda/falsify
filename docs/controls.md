# Security controls, each demonstrated failing closed

Enforcement is the claim, so each control below has a negative test that the
pipeline refuses. These are not prompt instructions; they are mechanism.

**The realistic attack:** a prompt-injected MR that talks the Falsifier into
writing somewhere it should not, or into editing `.gitlab-ci.yml` on its
scratch branch.

## Control 1 — Experiments execute with no credentials

Removing protected variables is **not** a credential-free environment. Every
job carries `CI_JOB_TOKEN` and may carry registry credentials.

So the `experiments` job separates **preparation** from **execution**:

| Phase | Runs as | Has |
| --- | --- | --- |
| Preparation | the job shell (trusted) | Full job environment; fetches experiments, prepares the checkout |
| Execution | a child process | `env -i` plus only the variables the tests need |

The child additionally runs:
- in a network namespace with no interfaces, **where the runner permits it**
- under a 10-minute job timeout and a 30-second per-test timeout
- under ulimit-level memory and process limits

Container-level resource limits are set in runner configuration **where the
project controls the runner.** This project does not claim them on shared
runners.

Results are collected by the trusted shell after the child exits. The
`certificate`, `build`, and `deploy-*` jobs never execute experiment code.

**Negative test:** `.falsify/controls/probe_job_token.py` — an experiment that
reads `CI_JOB_TOKEN` and asserts it is present. It must report the variable as
absent.

## Control 2 — Scratch branch confined to `.falsify/`

The Falsifier writes only to `falsify/mr-<iid>`. Three layers, not one:

1. The Falsifier's write tool is configured with a **fixed branch parameter**
   the model cannot override (pending Oct 9 question Q2).
2. Every other write path is **left out of its toolset**.
3. The `experiments` job does a shallow fetch of that branch and **refuses to
   proceed** if the branch diff touches anything outside `.falsify/`.

Layer 3 holds even if layers 1 and 2 turn out to be unavailable.

Experiments are then copied into the MR head checkout before pytest runs — so
they execute against MR code without ever living on the MR branch.

The scratch branch is deleted by `ledger-commit` after merge.

**Negative test:** a scratch commit that touches `.gitlab-ci.yml`. The
`experiments` job must fail with a branch-scope violation before running any
test.

## Control 3 — Authorization bound to head and claims version

The `certificate` job fails if no valid Gate 2 authorization exists for the
current head SHA and claims version. See [gates.md](gates.md) for the full
invalidation table.

**Negative test:** authorize experiments at head A, push head B, certify. The
job must refuse with a stale-authorization error.

## Control 4 — Promotion enforced at the merge gate

A remedy-accepted refutation counts as resolved only when the rerun is green
**and** the promoted file is present at the MR head with the hash recorded at
promotion time.

GitLab suggestions can only change lines already in the diff and cannot create
a file. So `promote` is a separate manual job: the human runs it, and it copies
the experiment byte-for-byte into `tests/` and records the hash.

The job commits with a **project access token**, not `CI_JOB_TOKEN` — a
`CI_JOB_TOKEN` push would not start a pipeline, and the new pipeline is what
re-certifies.

**Negative test:** accept a remedy, skip `promote`, certify. The job must
refuse with a missing-promotion error.

## Control 5 — No stored cloud credentials

Cloud deployment never uses stored secrets. `deploy-*` jobs authenticate with
GitLab's **OIDC ID token**, exchanged through Workload Identity Federation.

The WIF attribute condition requires:
- the project path
- the **protected environment** claim

So a job on a scratch branch, on an MR branch, or in any other project gets no
cloud identity at all.

**Negative test:** attempt the token exchange from a job without a protected
environment. The exchange must be refused by Google, not by a conditional in
the pipeline.

## Control 6 — Agents never touch the record

The ledger is written **only** by CI on `main` — `ledger-commit` and the
`deploy-*` / `prod-watch` / `rollback` jobs. No flow has write access to it,
and nothing is ever committed to an MR branch by the ledger.

Service accounts hold **Developer**, which cannot push to protected branches
and cannot deploy to the staging or production protected environments. They
hold no cloud identity.

## Control 7 — `live-experiments` has exactly one permitted destination

`live-experiments` is a different job with a different boundary from
`experiments`: it is allowed to reach **exactly one host**, the staging URL,
and nothing else. Rate-limited, with the thresholds committed to
`.falsify/thresholds.yaml` so the demo is reproducible.
