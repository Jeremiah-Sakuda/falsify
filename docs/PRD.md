# Falsify PRD

Oct 7, 2026 · @Jeremiah Somoine

## 1. Summary

Falsify is an AI code reviewer that cannot call something a defect unless it produces a reproducible failing test in the merge request's own pipeline. It is a Path A, Assisted-tier entry to the GitLab Transcend "Life After Code" Hackathon (Devpost, submissions close Oct 27, 2026, 9:00am EDT, so the working deadline is Oct 26), built on the GitLab Duo Agent Platform and deployed on Google Cloud Run.

The one rule: no red test, no accusation. A functional defect finding is a CI job, not a sentence. The human can reject the finding's interpretation of the spec. When the human accepts a finding, its evidence becomes a regression test that must be in the suite before the MR can merge. The human never writes code; the human only rules.

Prize targets: Best Assisted Agent (Path A, $4,000) plus one special prize, Most Stages Covered (Path A, $5,000) or Most Creative ($4,000), at the judges' discretion. Google Cloud deployment adds up to 0.2 bonus points on a 5.0 scale.

Short version of the loop: issue → falsifiable claims → MR → conjectures → approved experiments → red test → human ruling → fix as a suggestion → test promoted by a human-run job → ledger gate → staging (human-run) → merge → production approval → production watch → motion as an incident, if any.

Falsify runs alongside GitLab Duo Code Review rather than replacing it: Duo reads and comments, Falsify is only allowed to run experiments.

## 2. Problem

AI code reviewers produce statements, and statements cannot be trusted at scale. A reviewer that says "this pagination looks off by one" might be right, might be guessing, and the developer has to investigate either way. After enough unverified findings, teams turn the reviewer off or stop reading it.

Three specific failures drive that outcome:

- **Unsupported findings.** The reviewer asserts a defect with no reproduction. The developer pays the verification cost the tool should have paid.
- **Approval drift.** A single reviewer agent is rewarded for being agreeable and drifts toward LGTM. Real defects pass because nobody was assigned to break the change.
- **No audit trail.** When an agent reviews, fixes, and deploys, there is no record a second person can inspect of what was claimed, what was checked, and who decided. Regulated teams cannot adopt agentic review on those terms.

The post-code lifecycle inherits all three. If the review stage is unverifiable, every downstream gate (deploy, flag, rollback) is built on an opinion.

## 3. Audience and impact

Primary audience for the demo: solo builders and tiny teams with no second reviewer. Every project the author has shipped since January 2026 was a solo build; the only reviewer was the author. Falsify is the adversarial second reviewer that solo builders never have, and it leaves behind tests rather than comments.

Secondary audience for the write-up: teams that have turned AI review off, or never turned it on, including regulated teams that need every AI decision attributable and reviewable after the fact. The ledger (section 10) is the artifact they can hand to an auditor.

What the audience gains, measurably:

- Zero unsupported functional findings. Every functional defect claim comes with inspectable execution evidence: the test, both head runs, the base run, the pipeline and job IDs.
- Every accepted refutation leaves behind a regression test, enforced at the merge gate, so a found defect cannot come back unnoticed.
- A complete record of claims, evidence, and human rulings, kept in the repository and tied to the exact commits and artifacts it describes.

The impact case is made in the video by a side-by-side comparison against vanilla GitLab Duo code review on the same merge requests (section 13).

## 4. Product principles

**Governing rule.** Falsify may only make a functional defect claim through a reproducible failing experiment: FAIL on the MR head, reproduced on a second run, PASS on the merge base. Anything else it says (claims, conjectures, cost estimates, corroborations) is explicitly not a defect claim and is labeled as such. Three other kinds of evidence exist in the system, each under its own standard, and none borrows the functional refutation's guarantee: a new-feature contract failure (the experiment targets code with no base version, so it shows a possible violation of an approved claim, not a regression), a security finding (a scanner's report, ingested as-is), and an operational motion (a threshold crossed in a production window, which supports a response but does not by itself attribute cause to the MR).

**Secondary rule.** Falsify distrusts the MR; the infrastructure distrusts Falsify. Experiments are AI-generated code, so the job that runs them has no credentials, no secrets, no outbound network, and bounded CPU and wall time. The scratch branch the Falsifier writes to is unprotected, so its own pipeline receives no protected variables and can deploy nothing, even if the Falsifier edits `.gitlab-ci.yml` there.

**Division of authority.** The machine formulates and executes challenges. The human decides what the software ought to do. Every gate is a judgment, never a task.

**Agents never touch the record.** The ledger is written by a deterministic CI job from pipeline artifacts. No flow has write access to it.

**Human lands every test, and the gate checks that it landed.** A promoted regression test reaches the MR branch only when the human runs the manual promote job. GitLab suggestions can only change lines already in the diff and cannot create a file, so the job copies the experiment byte-for-byte into `tests/` and records its hash. A remedy-accepted refutation counts as resolved only when the rerun is green and the promoted file is present at the MR head with the recorded hash; a sustained contest resolves without promotion. The original failing evidence stays in the record; it is never overwritten by the later PASS.

**Precision in claims about the product.** The write-up says: every reported functional refutation includes inspectable execution evidence, and the human decides whether that evidence establishes a defect. It says unsupported functional findings are impossible. It does not say false positives are impossible (two assertion failures establish an observed result in a particular harness, not a correct reading of the spec), does not say hallucinations are impossible, and does not say flakiness is eliminated. The pitch line is: our AI must bring evidence, you can reject its interpretation, and when you accept the finding the evidence becomes a test that protects future changes.

**Non-goals for this submission:** multi-language support (Python only), IDE integration, replacing the base test suite, fully autonomous merge (that is the Hands-off tier, a different entry).

## 5. Vocabulary

Used consistently in flow prompts, MR comments, labels, the ledger, and the video.

| Term | Meaning | Where it appears |
| --- | --- | --- |
| Hypothesis | The MR's implicit claim: this change is safe to ship | Certificate header |
| Claim | A falsifiable acceptance criterion derived from the issue, with a number or a concrete condition; versioned (claims v1, v2) | Plan flow output, Gate 1 |
| Unfalsifiable | A requirement with no testable condition ("should be fast"); bounced back for a number | Plan flow output |
| Conjecture | A specific way the change could fail, tied to a claim or a diff hunk | Trial flow, Gate 2 |
| Experiment | The pytest file that fails if the conjecture is true; identified by its content digest | `.falsify/experiments/` on the scratch branch |
| Functional refutation | Experiment is FAIL on MR head twice and PASS on base; the strongest evidence type | experiments job result, MR comment |
| Contract failure | Experiment is FAIL on MR head twice and has no base version (new code); a possible violation of an approved claim, not a regression | experiments job result |
| Security finding | A scanner result (SAST, dependency, secret) ingested in ledger format; the scanner's evidence, not Falsify's | Security reports, certificate |
| Operational motion | A threshold crossed in the production watch window, with the requests that reproduced it; supports a response, does not prove the MR caused it | Monitor flow, Gate 4, incident |
| Corroboration | Experiment passed on MR head; a survived attempt, not proof | experiments job result, certificate |
| Error | Experiment could not run (import, fixture, timeout); not a finding of any kind | experiments job result |
| Contest | Advocate argues the experiment encodes the wrong spec | Trial flow, Gate 3 |
| Strike | Human sustains a contest; experiment is discarded and counted | Gate 3, certificate |
| Remedy | Advocate's proposed code fix, posted as a GitLab suggestion on lines in the diff | MR thread |
| Promotion | Human runs the manual promote job; the experiment is copied byte-for-byte into `tests/` and its hash recorded; required to resolve a remedy-accepted finding | MR branch, certificate |
| Certificate | Immutable pre-merge evidence record bound to head SHA, base SHA, claims version, experiment digests, pipeline and job IDs, and the identities of the humans who ruled | `ledger/mr-<iid>/certificate.md` |
| Events | Append-only post-merge history (image digest, deploys, approvals, motions, rollbacks) that references the certificate | `ledger/mr-<iid>/events.md` |

## 6. The loop across nine stages

Every stage is touched by something that does real work, not a placeholder job. Stages run in this order for each MR.

| Stage | What happens | GitLab feature used | Human gate |
| --- | --- | --- | --- |
| Plan | Plan flow rewrites the issue's acceptance criteria as falsifiable claims and bounces unfalsifiable ones | Custom flow, mention trigger, issue comments, labels | Gate 1: approve claims |
| Create | Developer pushes the MR and assigns the Falsify service account as reviewer; the Advocate writes code fixes as suggestions and the Falsifier writes tests on a scratch branch | Merge requests, assign-reviewer trigger, MR suggestions, branches | Suggestions applied by the human |
| Verify | Trial flow posts conjectures; experiments job runs approved experiments twice on MR head and once on base; human-run promote job lands accepted tests | Custom flow with Human Input, CI/CD pipelines, pipeline artifacts, manual jobs | Gate 2: approve experiments |
| Secure | SAST, dependency scanning, and secret detection run in the same pipeline; findings are ingested as refutations in ledger format | Security scanning templates, security reports | Rulings at Gate 3 |
| Verify (cont.) | Advocate posts a remedy or contest per refutation; human rules | MR suggestions, MR threads, labels | Gate 3: rule per refutation |
| Package | With the ledger job green, the image is built, tagged with the ledger hash, and pushed to the GitLab Container Registry and to Artifact Registry | Container Registry, container build job | None |
| Release | Staging deploy is a manual job the human runs on the MR; production deploys from main after merge, behind deployment approval on a protected environment | Environments, protected environments, deployment approvals, manual jobs | Human runs staging; Gate 4: approve production |
| Configure | Infrastructure for both environments is defined in `deploy/` and applied from CI; changes flagged high blast radius additionally ship behind a native Feature Flag, created off | Infrastructure code in the repo, CI-applied configuration, Feature Flags (Unleash) | Flag toggled by human after ruling |
| Monitor | prod-watch samples production metrics after the deploy; Monitor flow reads them and files at most one motion as a GitLab incident | Observability stack, Cloud Run metrics, incidents, custom flow | Gate 4 (cont.): rule on motion |
| Govern | ledger job gates merge; post-merge job writes `ledger/mr-<iid>.md`; approval rules require ledger green plus human approval; audit events record the rest | Merge request approval rules, protected branches, audit events | Enforced, not a click |

Each project may win one Path prize and one special prize. Most Stages Covered is judged on stages touched "in the most creative way," so the table above is also the argument for that prize.

## 7. Gates: the four human decisions

Four judgment gates, and a set of smaller human actions around them (applying suggestions, running promote, running staging, approving and starting production, mentioning Monitor, handling rollback). The Assisted claim rests on two facts rather than on the count: every agent action is bounded by a human authorization that names exactly what it covers, and only deterministic CI (tests, scans, build, certificate) runs without one. Whether that reading of "approve every step" satisfies the organizers is their call; the PRD argues it, it does not assume it. Every authorization is read from GitLab identity and structured state (an approval, a comment by a Maintainer in the fixed `falsify:` syntax, a manual job run), never from an LLM deciding whether a comment sounded like approval.

**What invalidates an authorization.** An authorization is bound to the exact things it covered. A new MR head invalidates Gate 2 and any unpromoted Gate 3 rulings and requires re-running the approved experiments; a new claims version invalidates Gate 2; a changed experiment digest invalidates the ruling on that experiment. A re-run of the same experiment digests against a new head is permitted without a new Gate 2.

**Gate 1, approve claims (issue).** The Plan flow comments with the rewritten acceptance criteria, each numbered (C1, C2…) and versioned (claims v1), and lists any it bounced as unfalsifiable with the question it needs answered. The human edits if needed, then posts `falsify: claims approved v1` as a comment. The certificate job later verifies that comment's author holds Maintainer and that its version matches the claims the experiments targeted. A label (`falsify::claims-approved`) is applied for visibility only; it carries no authority, since no label-change trigger is documented.

**Gate 2, authorize experiments (MR, inside the Trial flow).** The flow pauses at a Human Input component after posting five conjectures, each with: the claim or diff hunk it targets, the experiment it will write, and an estimated runtime. The human approves all, or strikes any by number. This is an authorization of a bounded operation (write up to five pytest files under `.falsify/experiments/` on the scratch branch and run them in the sandboxed job), not an approval of code that does not yet exist. The exact files are reviewable afterward by their digests in the certificate, and the human can strike any at Gate 3. Striking at Gate 2 is recorded as `struck-pre-run`.

**Gate 3, rule per finding (MR, inside the Trial flow).** For each functional refutation or contract failure, the Advocate posts either a remedy (a GitLab suggestion on the exact lines in the diff) or a contest (the experiment encodes the wrong spec, with reasoning). The flow pauses. The human does one of: apply the suggestion (remedy accepted), reply `falsify: sustain X3` to a contest (experiment struck, counted as `struck-wrong-spec`), or reply `falsify: overrule X3` (Advocate must produce a remedy instead). Resolution rules: a remedy-accepted finding is resolved only when the experiment reruns green on the new head and the human has run promote so the file is present at the head with its recorded hash; a sustained contest is resolved by the ruling alone. Because a CI job does not change its result when someone replies to a thread, the Trial flow starts a new MR pipeline after rulings are posted, and the certificate job on that pipeline reads the rulings and recomputes. Security findings are resolved the same way (remedy or a documented accept-risk ruling).

**Gate 4, approve production and rule on the motion.** Before this gate the human has already run the manual `deploy-staging` job on the MR and seen the live-experiments result (functional replay of the conjectures over HTTP, both flag states), so staging findings inform the merge decision rather than surprising anyone later. After merge, the main pipeline verifies the certificate against the merge commit, builds, records the image digest, and offers `deploy-prod`, which is GitLab's native deployment approval on the protected production environment, followed by the human starting the job (approval alone does not start it). After the deploy, prod-watch samples production for ten minutes and verifies the running revision's image digest matches the one recorded in events. The human then mentions the Monitor flow's service account on the MR; the flow reads the prod-watch artifact and files at most one operational motion as a GitLab incident linked to the MR and its certificate. The human replies `falsify: rollback` (runs the rollback job) or `falsify: deny` (recorded; incident closed). A motion is an observation in a window, not proof the MR caused it; the incident says so.

## 8. Flows

Three custom flows, defined as YAML under `.gitlab/duo/flows/`, enabled in the project, each with its own trigger. The design respects two platform constraints confirmed in current GitLab docs: a trigger must be performed by a human user (a flow, bot, or service account cannot fire one), and custom flows can pause at a Human Input component or with `require_tool_approval`. So Falsifier and Advocate are components of one flow rather than two flows that signal each other.

Each flow runs to completion in its own session. The Trial flow is the only one that pauses, twice, and both pauses are the human's judgment.

**Plan flow (`plan.yaml`).** Trigger: mention. Toolset: read issue, read project files, post comment. Prompt contract: output a numbered list of claims (C1…Cn), each with a testable condition; a separate list of bounced criteria, each with the one question needed to make it testable. Never invents numbers; asks for them.

**Trial flow (`trial.yaml`).** Trigger: assign reviewer. Components in order:

1. `falsifier` agent component. Inputs: MR diff, the approved claims comment, base test file list. Toolsets: read-only GitLab API (MR, diffs, files, pipelines, security reports) plus write to a scratch branch `falsify/mr-<iid>` only. Output: five conjectures in a fixed schema (id, target claim or hunk, conjecture, experiment summary, estimated runtime in seconds).
2. Human Input (Gate 2).
3. `falsifier` again, now writing one pytest file per approved conjecture to `.falsify/experiments/<id>_test.py` on the scratch branch. A scratch push does not re-run the MR pipeline on its own, so the component then starts a new pipeline on the MR branch through the API (the pipeline-run tool, or a pipeline trigger token held by the flow) and polls it until the experiments job finishes. Confirming which of those two works is an Oct 9 question.
4. `advocate` agent component. Inputs: the experiments artifact (per experiment: status FAIL/PASS/ERROR on head, status on base, both runs), the diff, the claims. Toolset: read-only plus MR suggestions and MR comments. Output per refutation: a remedy (suggestion on exact lines in the diff; never a new file) or a contest with reasoning.
5. Human Input (Gate 3).
6. Summary comment and exit. Open refutations remain visible on the MR; re-running the flow after fixes re-enters at step 3 for the open set only.

**Monitor flow (`monitor.yaml`).** Trigger: mention, after the production deploy. Toolset: read pipeline artifacts from the main pipeline, read the prod-watch metrics artifact, create incident, post comment. Output: at most one motion in a fixed schema (metric, threshold, observed value, the request IDs that reproduced it, recommendation), filed as a GitLab incident linked to the MR. An MCP server exposing Cloud Run metrics is an optional upgrade; the artifact path is the dependable one.

**Service accounts:** one per flow, named by the platform (`ai-<flow>-gitlab-duo` pattern), with Developer role. Developer permits pushes to any unprotected branch, so the scratch-branch restriction is enforced in three layers rather than by prompt: the Falsifier's write tool is configured with a fixed branch parameter the model cannot override (the flow framework's fixed tool parameters), every other write path is left out of its toolset, and the experiments job refuses any scratch branch whose diff touches files outside `.falsify/`. Service accounts cannot push to protected branches, cannot deploy to the staging or production protected environments, and hold no cloud identity. Whether the configured tools support the branch binding is a week-one test, not an assumption.

## 9. Pipeline

One `.gitlab-ci.yml` with stages that line up with the lifecycle. Every job below runs on merge request pipelines; deploy jobs also run on main.

| Job | Stage | Runs on | What it does | Needs | Output |
| --- | --- | --- | --- | --- | --- |
| base-tests | verify | MR, main | Runs `tests/` with pytest and coverage | | JUnit report, coverage artifact |
| experiments | verify | MR | Fetches `.falsify/experiments/` from `falsify/mr-<iid>`; rejects the branch if it touches any file outside `.falsify/`; runs each file twice against MR head and once against the merge base, inside the execution boundary described below | base-tests | `experiments.json` (per experiment: digest, head run 1, head run 2, base run, classification) |
| sast, dependency-scan, secret-detect | secure | MR, main | GitLab security templates | | Security reports |
| certificate | govern | MR | Deterministic script: binds head SHA, base SHA, claims version, experiment digests, pipeline and job IDs, rulings (verified by author role and `falsify:` syntax), and promotion hashes into a certificate; fails if any finding is unresolved, if any remedy-accepted finding lacks its promoted file at the head, or if no Gate 2 authorization exists for this head and claims version | experiments, scans | `certificate.md` artifact plus its hash |
| promote | verify | MR, manual | Human-run; copies the named experiment byte-for-byte into `tests/`, commits to the MR branch with a project access token (a `CI_JOB_TOKEN` push would not start a pipeline), records the file hash, and the push starts a new MR pipeline | experiments | Commit, new MR pipeline |
| build | package | MR, main | Builds the container, tags with short SHA and certificate hash, pushes to the GitLab Container Registry and Artifact Registry, records the image digest | certificate (MR) / certificate-verify (main) | Image, digest |
| deploy-staging | release | MR, manual | Human-run; deploys the MR image to Cloud Run `falsify-staging` by image digest, authenticating with the job's OIDC ID token under a WIF condition that requires this project and the staging environment | build | Environment URL |
| live-experiments | monitor | MR | Replays conjectures as HTTP against the staging host only (its one permitted destination), once per feature flag state, at low rate; functional check, informs Gate 4 | deploy-staging | `live.json` |
| certificate-verify | govern | main | Fetches the merged MR's certificate artifact, confirms the merge commit's tree matches the certified head (or a documented merge of it), and that all promoted files are present with their hashes; the main pipeline cannot proceed without it | | Verified certificate |
| ledger-commit | govern | main | Writes `ledger/mr-<iid>/certificate.md` (immutable, hash recorded) and opens `events.md`; regenerates the `LEDGER.md` index | certificate-verify | Commit to main (`[skip ci]`) |
| deploy-prod | release | main, manual | Behind deployment approval on the production protected environment, then started by the human; deploys by the recorded image digest; appends a deploy event | build, ledger-commit | Environment URL, event |
| prod-watch | monitor | main | Verifies the live revision's digest, then samples production error rate and p95 latency for 10 minutes while replaying the MR's conjectures at production-like rate; appends a watch event with thresholds crossed and request IDs | deploy-prod | `watch.json`, event |
| rollback | release | main, manual | Routes traffic to the previous Cloud Run revision; appends a rollback event | | Event |

**Experiments job contract.** A refutation is recorded only when all of the following hold:

1. The experiment's result on the MR head is FAIL (an assertion failed), not ERROR (import error, fixture error, timeout, collection error).
2. The same FAIL reproduces on a second run on the MR head.
3. The experiment's result on the merge base is PASS, or the experiment targets a file that does not exist on the base (new code), in which case the base run is recorded as `n/a`.

Anything else is recorded as corroboration (PASS on head), error (ERROR anywhere), or not-attributable (FAIL on base too). Errors are reported back to the Falsifier for one rewrite attempt per experiment; a second error discards it.

**Execution boundary.** Removing protected variables is not a credential-free environment: every job carries `CI_JOB_TOKEN` and may carry registry credentials. So the experiments job separates preparation from execution. The job shell (trusted) fetches the experiments and prepares the checkout; execution of pytest happens in a child process started with a scrubbed environment (`env -i` plus the handful of variables the tests need), in a network namespace with no interfaces where the runner permits it, under a 10-minute job timeout, a 30-second per-test timeout, and ulimit-level memory and process limits; container-level resource limits are set in runner configuration where the project controls the runner, and the PRD does not claim them on shared runners. Results are collected by the trusted shell after the child exits. live-experiments is a different job with a different boundary: it is allowed to reach exactly one host, the staging URL, and nothing else. Cloud deployment never uses stored secrets; `deploy-*` jobs authenticate with GitLab's OIDC ID token, and the Workload Identity Federation attribute condition requires the project path and the protected environment claim, so a job on a scratch branch or any other project gets no cloud identity at all. The certificate, build, and `deploy-*` jobs never execute experiment code.

**Scratch branch mechanics.** The Falsifier writes only to `falsify/mr-<iid>`. The experiments job does a shallow fetch of that branch, refuses to proceed if the branch diff touches anything outside `.falsify/` (a prompt-injected MR that talks the Falsifier into editing CI config is the realistic attack), then copies `.falsify/experiments/` into the MR head checkout before running pytest. Experiments run against MR code without ever living on the MR branch. Because a scratch push does not re-run the MR pipeline, the Trial flow starts a new MR pipeline through the API after pushing. Promotion is a human act: the human runs the promote job with the experiment ID, and the job copies the file into `tests/` and commits. The scratch branch is deleted by ledger-commit after merge.

## 10. The ledger

The ledger is two files per merged MR under `ledger/mr-<iid>/`, plus a generated `LEDGER.md` index at the repository root. `certificate.md` is the immutable pre-merge evidence record: it binds head SHA, base SHA, claims version, every experiment's digest and runs, every scanner finding, every ruling with the ruling human's GitLab identity, and every promoted file's hash, and its own hash is recorded in the index and in the image tag. `events.md` is append-only post-merge history: image digest, staging and production deploys, approvals, watch results, motions, rollbacks, each referencing the certificate hash. Splitting them is what lets the record describe production events that happen after it was certified without ever changing what was certified. All three files are written only by CI on main (ledger-commit and the `deploy-*`/prod-watch/rollback jobs); no agent has write access, nothing is ever committed to an MR branch by the ledger, and the certificate job on the MR pipeline is what gates merge.

Certificate structure (illustrative; `events.md` for the same MR would list the image digest, the staging deploy, the production approval and start with identities, the watch result, and any motion, each with a timestamp and the certificate hash):

```markdown
# Certificate · MR !42 · Add scholarship deadline filter
head 7f3a9c2 · base 1b2e4d0 · claims v2 · pipeline 1842211 · certified 2026-10-19T18:42Z
Hypothesis: this change is safe to ship. Status: CERTIFIED (0 unresolved findings)
Gate 1: claims v2 approved by @jsakuda (Maintainer) · Gate 2: experiments X1 to X5 authorized by @jsakuda for head 7f3a9c2

| ID | Kind | Conjecture | Target | Digest | Head | Base | Ruling | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| X1 | functional refutation | Deadline compared in server time, not applicant zone | C2 / api/deadlines.py:41 | a91f… | FAIL, FAIL | PASS | remedy applied by @jsakuda | rerun PASS at 7f3a9c2; promoted tests/test_deadlines_tz.py (a91f…) |
| X2 | functional refutation | Pagination drops last record when total % page == 0 | C1 / api/list.py:18 | 3c77… | FAIL, FAIL | PASS | remedy applied by @jsakuda | rerun PASS; promoted tests/test_pagination_edge.py (3c77…) |
| X3 | functional refutation | Negative GPA accepted | C3 / api/eligibility.py:9 | e02b… | FAIL, FAIL | PASS | contest sustained by @jsakuda: spec allows null, not negative; test asserted null | struck-wrong-spec |
| X4 | corroboration | Concurrent applications double-count | C1 / api/apply.py | 5d10… | PASS, PASS | PASS | | |
| X5 | error | Unicode name breaks CSV export | C1 / api/export.py | 88ab… | ERROR | | | discarded after one rewrite |
| S1 | security finding | CVE-2026-XXXX in requests 2.28 | dependency scan, report 9931 | | | | remedy applied by @jsakuda | pin bumped; scan clean at 7f3a9c2 |

Counts: 3 functional refutations, 1 corroboration, 1 error, 1 struck, 1 security finding. Unsupported functional findings: 0.
```

The table is illustrative; real entries come from real runs. The CVE identifier is a placeholder.

**Approval rules on the main branch:** at least one human approval (service accounts excluded from eligible approvers); the certificate job must pass; the pipeline must succeed. Protected branch settings prevent the service accounts from pushing to main, and protected environments prevent them from deploying anywhere. Audit events are on for the project, so Gate 4 approvals, flag toggles, and incident actions appear in the audit log without extra work.

**Solo-owner configuration, stated plainly.** By default GitLab stops an MR author from approving their own MR and stops the person who ran a deployment pipeline from approving its deployment. For a single builder, both settings are relaxed in the project configuration, and the repository README says so: the separation of duties in that configuration is between the agent and the human, not between two humans. A team configuration keeps the defaults and requires an independent approver. The two are documented as different guarantees, not the same one.

## 11. The demo application

The app is scenery. It exists to give the Falsifier real surface and the video a believable story. Build it in one day and never polish it.

What it is: a scholarship eligibility and deadline API in FastAPI with SQLite (Postgres optional), Python 3.12. Endpoints:

- `POST /scholarships` and `GET /scholarships?page=&size=` (paginated listing)
- `GET /scholarships/{id}/eligible?gpa=&country=&tz=` (eligibility rules: GPA threshold, country allowlist, deadline not passed in the applicant's time zone)
- `POST /applications` (one per applicant per scholarship; concurrent safety matters)
- `GET /export.csv` (CSV of applications, Unicode names)
- Bearer token auth on write endpoints
- Amounts stored in the smallest currency unit as integers

Why this shape: dates across time zones, pagination, money, auth, concurrency, and text encoding are the six classic places subtle bugs live, and every one maps to a conjecture type the Falsifier is prompted to prefer (boundary, concurrency, spec violation).

## 12. Seeded-defect corpus

**Held out of this repository by design.**

The twelve seeded defects (D1-D12), their files, kinds, and the baseline
prediction table live in `planning/corpus.md`, which is untracked
(see `.gitignore`). Section 14 requires that seed descriptions, reference
fixes, and evaluation metadata stay "outside the repository and outside any
agent's reachable context" - and the Falsifier reads this repository. Putting
the corpus in a committed file would hand the agent the answer key and void
the held-out half of the evaluation.

What is safe to state here:

- Twelve defects are seeded, each introduced in its own small MR so results
  are attributable.
- They span six bug-prone surfaces: time zones, pagination, money,
  auth, concurrency, and text encoding.
- Six (D1-D6) are the tuning half; six (D7-D12) are held out until the
  prompt freeze. The evaluation reports the halves separately.
- Two further MRs are unseeded: one clean change, and one written the day of
  filming that the Falsifier prompt never saw.
- The corpus is disclosed on screen in the submission video, after the
  measurements are taken.

## 13. Google Cloud deployment

Deployment is optional for Path A and done anyway: Release, Configure, and Monitor need a running service, and the Cloud Run deployment earns up to 0.2 bonus points. The URL submitted for the bonus is the production service, kept at one minimum instance so it answers immediately, with a landing page at `/` (the one rule, a link to the ledger, and the API docs) so a judge who clicks sees something. Deployment code lives in the public repository, and the service stays live through the winners' announcement (around Nov 16, 2026).

| Piece | Choice | Notes |
| --- | --- | --- |
| Compute | Cloud Run, two services: `falsify-staging`, `falsify-prod` | Staging scales to zero; production min instances 1 and max instances 1 through Nov 16 (see Database) |
| Image | GitLab Container Registry (pipeline's registry) and Artifact Registry (Cloud Run's), tagged `<short-sha>-<certificate-hash>` and deployed by digest | The tag ties every revision to its certificate; the digest in `events.md` is what prod-watch verifies against the live revision |
| Deploy identity | GitLab OIDC ID token exchanged through Workload Identity Federation | No stored cloud secrets anywhere; the WIF attribute condition requires the project path and the protected-environment claim, so only `deploy-*` jobs for staging/production get an identity |
| Database | SQLite file on the instance filesystem for the demo, max instances 1 | Cloud Run's filesystem is instance-local and ephemeral; the demo state is disposable and reset by a job. The concurrency defect (D3) is tested within one instance, and the write-up says so. Cloud SQL only if time allows |
| Feature flags | GitLab Feature Flags (Unleash) with the Unleash client in the app | live-experiments runs both states; an extra on top of the infra code that anchors Configure |
| Observability | GitLab observability stack from the workspace onboarding plus Cloud Run request metrics | prod-watch samples error rate and p95 latency for 10 minutes after each production deploy |
| Rollback | `gcloud run services update-traffic` to the previous revision | Triggered by the manual rollback job; appends an event |
| Region | us-east1 | Nearest to the author; irrelevant to judging |

Infrastructure code in `deploy/`: a `cloudrun.yaml` per environment, a `setup.sh` that creates the services, registry, and WIF binding once, and the CI jobs that call them. Nothing is created by hand after setup.

## 14. Evaluation

The impact criterion asks whether the solution addresses the problem "based on what's demonstrated," so the submission carries a measured comparison rather than a claim. The comparison is between equivalent workflows: the baseline is Duo Code Review plus the same security scans, and the treatment is that baseline plus Falsify, on the same 14 MRs (12 seeded, 2 unseeded). Scanner-originated findings are counted separately from agent-generated experimental findings in both conditions, so Falsify is never credited for what the scanner found. The question the table answers is what adding Falsify catches or resolves that the baseline workflow does not, and at what human cost. It is described everywhere as a small controlled evaluation on one application, not evidence of broad superiority.

| Metric | Definition | Baseline (Duo review + scans) | Baseline + Falsify |
| --- | --- | --- | --- |
| Defects found, tuned half | Seeded defects identified among D1 to D6, scanner finds counted separately | measured | measured |
| Defects found, held-out half | Seeded defects identified among D7 to D12, prompt and configuration frozen before | measured | measured |
| Precision | Defect claims that correspond to a real defect, divided by all defect claims; a struck wrong-spec experiment counts against Falsify | measured | measured |
| Recall | Seeded defects found divided by 12; misses listed by ID | measured | measured |
| Unsupported functional findings | Functional defect claims with no reproducing test | measured | 0 by construction (reported, not compared) |
| Wrong-spec experiments struck | Red experiments the human ruled encoded the wrong spec | n/a | measured |
| Experiments that failed to run | ERROR outcomes, and how many were rescued by the one allowed rewrite | n/a | measured |
| Active human time per accepted finding | Minutes the human spent reading, ruling, applying, and promoting, divided by accepted findings | measured (review time per MR) | measured |
| Total review wall time per MR | Reviewer assignment to merge-ready | measured | measured |
| Compute and token cost per MR | CI minutes plus model tokens | measured | measured |
| Regression tests added | Experiments promoted into `tests/` across all MRs | 0 | measured |
| Corroboration-only runs | MRs where Falsify found nothing and said so | n/a | measured (target: the clean MR) |
| Prevented return | Seeded defects reintroduced in a follow-up change and caught by the promoted suite | n/a | measured (target: all promoted) |

Adjudication: a real bug found outside the seeded set is counted as a true positive only if a reference fix is written and the experiment passes against it. Seed descriptions, reference fixes, and evaluation metadata live outside the repository and outside any agent's reachable context. The freeze covers the Falsifier and Advocate prompts, the model and configuration, the experiment harness, the thresholds, and the procedure; it is recorded in the repo as a tagged commit. Both conditions run from the same starting state per MR, so tests promoted on earlier MRs do not advantage later measurements.

The honest framing in the write-up: Falsify cannot make an unsupported claim, Falsify can still be wrong about the spec, and the strike count is reported rather than hidden. "Falsify was wrong N times; here are the experiments I struck" is part of the narrative, not a footnote.

The comparison is run once the Falsifier prompt is frozen (end of week two). Tuning touches D1 to D6 only; D7 to D12 and the two unseeded MRs are first run after the freeze. Falsify is presented as a complement to Duo Code Review throughout: Duo reads and comments, Falsify runs experiments, and the two together are the pitch to a GitLab judge.

## 15. Demo video

Under three minutes, YouTube, public, no third-party trademarks or copyrighted music. Judges are not required to watch past 3:00. Four beats and a measured result, with the sustained contest given real time, because the agent being wrong and the human's rejection staying in the record is the clearest demonstration of why the design exists.

**Hook (0:00 to 0:12).** If you ship alone, nobody tries to break your code before it goes out. Falsify does, and it is only allowed to speak in failing tests. No red test, no accusation. (Audience named on screen: solo builders and small teams with no second reviewer.)

**Beat 1, the refutation (0:12 to 1:05).** An MR with one of the lead defects, chosen from the measured comparison. Duo Code Review's actual comment is shown as recorded, whatever it said. Falsify posts five conjectures; cut to the human approving them. Pipeline runs; one goes red. Show the generated test on screen for four seconds, long enough to read the assertion. Show the ledger line: FAIL, FAIL on head; PASS on base. That is the product.

**Beat 2, the ruling and the test (1:05 to 1:50).** First the contest, in full: the Advocate argues an experiment asserted the wrong requirement (null GPA versus negative), the human reads the test, replies `falsify: sustain`, and the strike stays in the certificate. Eight to ten seconds, enough for a judge to understand the test ran correctly and asserted the wrong thing. Then the remedy: the Advocate's suggestion on the exact lines, Apply, pipeline green, the human runs promote, the file lands in `tests/` with its hash. One line of narration: the review ends with a test that protects the next change.

**Beat 3, prevented return (1:50 to 2:05).** A follow-up change quietly reintroduces the deadline bug. The permanent suite goes red on the promoted test. Found it, fixed it, kept it out. This is the strongest proof of promotion and costs fifteen seconds.

**Beat 4, the motion (2:05 to 2:40).** Caption on screen: a separately disclosed, workload-dependent case; the ten-minute watch window is time-compressed. The human runs staging and approves and starts production. prod-watch verifies the live digest, then samples production under replayed load; p95 latency crosses the committed threshold on the N+1 (D11), which stayed under the line at staging's low rate. The Monitor flow files an incident linked to the certificate: metric, threshold, observed, revision digest, the requests that reproduced it, recommend rollback. The human replies. The incident text says it is an observation in a window, not proof of cause.

**Close (2:40 to 2:58).** The evaluation table, cut to one useful result and one honest limitation, held long enough to read (recall on the held-out half, and the number of experiments struck). Then the certificate for the MR, full screen, and the nine-stage strip as a two-second montage. Last line: our AI must bring evidence, you can reject its interpretation, and when you accept the finding the evidence becomes a test.

Production notes: screen recordings at 1080p, cursor visible, no face cam needed. A thin nine-stage indicator (plan, create, verify, package, secure, release, configure, monitor, govern) overlaid in the corner, lighting as each stage is touched, replaces any narration about package, configure, and govern. Captions on. The seeded defects are disclosed in a caption during Beat 1.

## 16. Submission package

Everything the Devpost form and the Official Rules ask for, as a checklist.

- [ ] Public GitLab project under the hackathon group, with an MIT LICENSE file detected and shown in the About section
- [ ] Visible CI/CD pipeline history showing experiments, ledger, promote, build, deploy-staging, live-experiments, an approved deploy-prod, and prod-watch runs
- [ ] `README.md` with setup instructions, the one rule, the vocabulary table, and how to run the flows
- [ ] `.gitlab/duo/flows/plan.yaml`, `trial.yaml`, `monitor.yaml` in the repo (subject to MIT and the GitLab DCO per the rules)
- [ ] `ledger/` with entries from all 14 evaluation MRs and the generated `LEDGER.md` index
- [ ] `deploy/` with Cloud Run code; the production URL (min instances 1, landing page at `/`) in the submission form for the Google Cloud bonus
- [ ] Demo video under 3:00 on YouTube, public, captions on, no trademarks or licensed music
- [ ] Text description: what it does, the problem, who it is for, how GitLab automates the post-code lifecycle, the evaluation table, and the complement-to-Duo framing
- [ ] Path selected: A (Start Fresh). Autonomy level: Assisted. Opt out of the Environmental prize (no sustainability claim made)
- [ ] Project created on or after Oct 5, 2026 (first commit date is the proof)
- [ ] Form submitted by end of day Oct 26; the Oct 27 9:00am EDT close is not a working window

Devpost fields, drafted in advance: tagline ("No red test, no accusation"), the 150-word summary, the "how we built it" paragraph naming flows, triggers, Human Input, security templates, protected environments, Feature Flags, and the observability stack by name, and the "challenges" paragraph that tells the wrong-spec story truthfully.

Prize framing in the description: Best Assisted Agent as the Path prize; Most Stages Covered and Most Creative both argued, with the nine-stage table and the one rule respectively, and the judges choose.

## 17. Risks, open questions, and cut order

**Platform risks, validated first.** Custom flows and triggers must be enabled in the provisioned group; confirm on day one before writing any YAML. Human Input is documented in the flow builder and `require_tool_approval` in the YAML schema, but the exact way a paused flow resumes from an MR comment needs a hands-on test. If pausing turns out to be chat-only, the fallback is the earlier design: each gate ends the flow and a human label change triggers the next one.

**Questions for the Oct 9 build session (Missy Davies and Dennis Meister):**

- Does a Human Input pause resume from an MR thread reply, a mention, or only from the session UI? (No label-change trigger is documented, so labels carry no authority in this design.)
- Can the Falsifier's write tool be given a fixed branch parameter the model cannot override, and can every other write path be left out of its toolset?
- From inside a flow, can the service account call `POST /projects/:id/merge_requests/:iid/pipelines` to start an MR pipeline (not a branch pipeline) after a push to the scratch branch? If not, what can?
- Does a pipeline that a human's push started count as human-initiated for a pipeline-event trigger, or only the push itself?
- Is an arbitrary HTTPS MCP server reachable from a flow on GitLab.com, or only catalog-vetted ones? (If only vetted, the metrics artifact path stands and MCP is dropped from the write-up.)
- Is there a per-session step or token cap that five conjectures plus five experiments plus the Advocate pass would hit?
- On the hackathon group's runners, can a job run a child process in a separate network namespace, and are container resource limits set in runner configuration?

**Quality risks.** The Falsifier's first ten experiments decide the project. If they are trivial ("does the function return"), the prompt gets rebuilt around the claims and the three preferred conjecture kinds before anything else is built. Wrong-spec experiments are expected; the contest path exists for them and the strike count is published.

**Demo risks.** Live experiments against staging must be rate-limited and the thresholds committed to the repo, so the motion in Beat 3 is reproducible on the day of filming. Record Beat 3 twice.

**Security risks.** The realistic attack is a prompt-injected MR that talks the Falsifier into writing somewhere it should not, or into editing `.gitlab-ci.yml` on its scratch branch. Controls: the write tool's fixed branch parameter and a toolset with no other write path; the experiments job rejecting any scratch branch that touches files outside `.falsify/`; execution of experiment code in a scrubbed child environment with no job token; cloud identity issued only through WIF conditions on the protected-environment claim, so no job on any scratch or MR branch can deploy; service accounts barred from protected branches and environments. Enforcement is the claim, so the README demonstrates each control failing closed: an experiment that tries to read `CI_JOB_TOKEN`, a scratch commit outside `.falsify/`, a stale Gate 2 against a new head, and a remedy-accepted finding with no promoted file, each refused by the pipeline.

**Cut order if something slips, in this sequence and no other:** Configure (feature flags in both states) first, scan ingestion into the certificate second, the MCP server third, the production motion fourth (the prevented-return beat replaces it in the video if it goes). The core loop, the certificate with enforced promotion, and the authorization binding are never cut: they are the product.

## 18. Build plan

The one milestone that matters is the first ten experiments on Oct 14: if they are good, the project works and the rest is additive; if they are trivial, the Falsifier prompt is rebuilt before anything else is touched. The prompt freeze on Oct 22 is what makes the evaluation honest, and the two unseeded MRs are written after it.

Definition of done per block:

1. **Confirm flows, triggers.** Custom flows and triggers enabled in the group (contributor onboarding is already approved); one trivial flow paused at a Human Input and resumed from an MR; a flow starts a new MR pipeline from inside a session; answers to the six Oct 9 questions written into this doc.
2. **Demo app + defects.** API running locally with base-tests green on a clean branch; 12 defect MRs opened as drafts; LICENSE, README, and the landing page at `/` in place.
3. **Core loop.** Plan flow posts claims on an issue; Trial flow posts conjectures, pauses, pushes experiments, starts the MR pipeline, and the experiments job records a refutation with head and base results on D1.
4. **Advocate, ledger, scans.** Suggestions land, promote lands a test with its hash, the certificate job blocks merge on an unresolved finding, a missing promoted file, or a stale Gate 2; certificate-verify and ledger-commit write the certificate and events files on main; dependency scan finding appears as S1.
5. **Cloud Run + flags.** Staging deploys from a manual job on the MR; production deploys from main behind approval; credentials scoped to protected environments; a Feature Flag toggles a change; image tagged with the ledger hash in both registries.
6. **Monitor flow, live tests.** live-experiments runs both flag states on staging; prod-watch reproduces D11 on production and the Monitor flow files one incident with the request IDs.
7. **Evaluation.** The table in section 14 filled from real runs on 14 MRs, tuned and held-out halves reported separately.
8. **Video.** Three beats recorded, Beat 3 twice, cut to under 2:50 with captions.
9. **Submit.** Devpost form complete and submitted by end of day Oct 26.

## 19. Sources

- GitLab Docs: Custom flows (Human Input component)
- GitLab Docs: Flow Registry Framework v1 (`require_tool_approval`, component inputs and toolsets)
- GitLab Docs: Triggers (trigger event types; human-initiated restriction)
- Hackathon overview and Official Rules, as shared in this conversation (prizes, paths, autonomy levels, submission requirements, judging criteria, Google Cloud bonus)
