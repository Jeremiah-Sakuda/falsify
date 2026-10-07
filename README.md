# Falsify

**No red test, no accusation.**

Falsify is an AI code reviewer that cannot call something a defect unless it
produces a reproducible failing test in the merge request's own pipeline.

A functional defect finding is a CI job, not a sentence. You can reject the
finding's interpretation of the spec. When you accept one, its evidence
becomes a regression test that must be in the suite before the MR can merge.
You never write code; you only rule.

Built on the GitLab Duo Agent Platform for the GitLab Transcend
**Life After Code** Hackathon — Path A (Start Fresh), **Assisted** autonomy
tier — and deployed on Google Cloud Run.

Falsify runs *alongside* GitLab Duo Code Review rather than replacing it:
Duo reads and comments, Falsify is only allowed to run experiments.

---

## The one rule

Falsify may only make a **functional defect claim** through a reproducible
failing experiment:

1. **FAIL** on the MR head (an assertion failed — not an import or fixture error)
2. The same FAIL **reproduces on a second run** on the MR head
3. **PASS** on the merge base

Everything else it says — claims, conjectures, corroborations, cost estimates
— is explicitly *not* a defect claim and is labeled as such.

Three other kinds of evidence exist, each under its own weaker standard, and
none borrows the functional refutation's guarantee:

| Kind | Standard | What it does *not* establish |
| --- | --- | --- |
| Contract failure | FAIL twice on head, no base version (new code) | Not a regression — a possible violation of an approved claim |
| Security finding | A scanner's report, ingested as-is | Not Falsify's evidence |
| Operational motion | A threshold crossed in a production window | Not that this MR caused it |

### What this does and does not claim

- ✅ Every reported functional refutation ships with inspectable execution
  evidence: the test, both head runs, the base run, the pipeline and job IDs.
- ✅ Unsupported functional findings are impossible.
- ❌ It does **not** claim false positives are impossible. Two assertion
  failures establish an observed result in a particular harness, not a
  correct reading of the spec.
- ❌ It does **not** claim hallucinations are impossible.
- ❌ It does **not** claim flakiness is eliminated.

The strike count — the number of times a human ruled that an experiment
encoded the wrong spec — is published, not hidden.

---

## The loop

```
issue
  └─> falsifiable claims ────────────────── Gate 1: approve claims
        └─> MR + reviewer assigned
              └─> conjectures ───────────── Gate 2: authorize experiments
                    └─> experiments run (head ×2, base ×1)
                          └─> refutation
                                └─> remedy or contest ── Gate 3: rule per finding
                                      └─> promote (human-run job)
                                            └─> ledger gate
                                                  └─> staging (human-run)
                                                        └─> merge
                                                              └─> production ── Gate 4: approve
                                                                    └─> prod-watch
                                                                          └─> motion as incident
```

## Vocabulary

Used consistently in flow prompts, MR comments, labels, the ledger, and the video.

| Term | Meaning |
| --- | --- |
| **Hypothesis** | The MR's implicit claim: this change is safe to ship |
| **Claim** | A falsifiable acceptance criterion derived from the issue, with a number or concrete condition; versioned (`claims v1`, `v2`) |
| **Unfalsifiable** | A requirement with no testable condition ("should be fast"); bounced back for a number |
| **Conjecture** | A specific way the change could fail, tied to a claim or a diff hunk |
| **Experiment** | The pytest file that fails if the conjecture is true; identified by its content digest |
| **Functional refutation** | FAIL on head twice, PASS on base. The strongest evidence type |
| **Contract failure** | FAIL on head twice, no base version (new code) |
| **Security finding** | A scanner result, ingested in ledger format |
| **Operational motion** | A threshold crossed in the production watch window |
| **Corroboration** | Experiment passed on head. A survived attempt, not proof |
| **Error** | Experiment could not run. Not a finding of any kind |
| **Contest** | Advocate argues the experiment encodes the wrong spec |
| **Strike** | Human sustains a contest; experiment discarded and counted |
| **Remedy** | Advocate's proposed fix, posted as a GitLab suggestion on lines in the diff |
| **Promotion** | Human runs the manual `promote` job; the experiment is copied byte-for-byte into `tests/` and its hash recorded |
| **Certificate** | Immutable pre-merge evidence record, bound to head SHA, base SHA, claims version, experiment digests, pipeline/job IDs, and the humans who ruled |
| **Events** | Append-only post-merge history that references the certificate |

## The four gates

Every authorization is read from GitLab identity and structured state — an
approval, a comment by a Maintainer in the fixed `falsify:` syntax, a manual
job run. Never from an LLM deciding whether a comment sounded like approval.

| Gate | Where | Human action | Syntax |
| --- | --- | --- | --- |
| **1** Approve claims | Issue | Edit the claims, then approve the version | `falsify: claims approved v1` |
| **2** Authorize experiments | MR (Trial flow pause) | Approve all, or strike by number | `falsify: approve all` / `falsify: strike X3` |
| **3** Rule per finding | MR (Trial flow pause) | Apply the suggestion, or rule on a contest | `falsify: sustain X3` / `falsify: overrule X3` |
| **4** Approve production, rule on motion | MR + environment | Native deployment approval, then start the job; then rule on the motion | `falsify: rollback` / `falsify: deny` |

### What invalidates an authorization

An authorization is bound to the exact things it covered.

- A **new MR head** invalidates Gate 2 and any unpromoted Gate 3 rulings.
- A **new claims version** invalidates Gate 2.
- A **changed experiment digest** invalidates the ruling on that experiment.
- A **re-run of the same experiment digests** against a new head is permitted
  without a new Gate 2.

## Trust boundaries

**Falsify distrusts the MR; the infrastructure distrusts Falsify.**

Experiments are AI-generated code, so the job that runs them has no
credentials, no secrets, no outbound network, and bounded CPU and wall time.
The scratch branch the Falsifier writes to is unprotected, so its own pipeline
receives no protected variables and can deploy nothing — even if the Falsifier
edits `.gitlab-ci.yml` there.

Four controls, each demonstrated failing closed (see `docs/controls.md`):

| # | Control | Demonstrated by |
| --- | --- | --- |
| 1 | Experiments run with a scrubbed environment and no job token | An experiment that tries to read `CI_JOB_TOKEN` |
| 2 | Scratch branch confined to `.falsify/` | A scratch commit touching a file outside it |
| 3 | Gate 2 authorization bound to head + claims version | A stale Gate 2 against a new head |
| 4 | Promotion enforced at the merge gate | A remedy-accepted finding with no promoted file |

Each is refused by the pipeline, not by a prompt.

## Repository layout

```
.gitlab/duo/flows/     plan.yaml, trial.yaml, monitor.yaml — the three custom flows
.gitlab-ci.yml         the nine-stage pipeline
app/                   the demo application (FastAPI + SQLite) — scenery
tests/                 the permanent suite; promoted experiments land here
scripts/               deterministic CI scripts (certificate, ledger, experiments harness)
.falsify/              thresholds, prompts, the experiments contract
deploy/                Cloud Run service definitions, WIF setup, infra as code
ledger/                mr-<iid>/certificate.md + events.md, written only by CI on main
evaluation/            the measured comparison against vanilla Duo review
docs/                  PRD, controls, gates reference, vocabulary
```

> `planning/` is untracked by design — it holds the seeded-defect corpus and
> reference fixes, which must stay outside the repository and outside any
> agent's reachable context until the video discloses them. See
> `docs/PRD.md` §12.

## Solo-owner configuration, stated plainly

By default GitLab stops an MR author from approving their own MR, and stops
the person who ran a deployment pipeline from approving its deployment. For a
single builder, **both settings are relaxed** in this project's configuration.

The separation of duties in that configuration is **between the agent and the
human, not between two humans.** A team configuration keeps the defaults and
requires an independent approver. These are different guarantees and are
documented as such.

## Running it

See [docs/setup.md](docs/setup.md) for the full walkthrough. Short version:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
uvicorn app.main:app --reload
```

## Non-goals for this submission

Multi-language support (Python only), IDE integration, replacing the base test
suite, fully autonomous merge (that is the Hands-off tier — a different entry).

## License

MIT — see [LICENSE](LICENSE).
