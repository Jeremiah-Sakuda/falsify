# Gates reference

The authoritative definition of every human authorization in Falsify: what it
covers, how it is read, and what invalidates it.

**Authorizations are read from GitLab identity and structured state only** — an
approval, a comment by a Maintainer in the fixed `falsify:` syntax, a manual
job run. Never from an LLM deciding whether a comment sounded like approval.
The parser is in `scripts/rulings.py` and is deliberately strict: an
unrecognized `falsify:` line is an error, not a guess.

## Comment syntax

Exact, case-sensitive, one directive per comment line. Anything else is
ignored (and, where a ruling was required, the certificate job fails).

| Directive | Gate | Effect |
| --- | --- | --- |
| `falsify: claims approved v<N>` | 1 | Binds claims version N as authorized |
| `falsify: approve all` | 2 | Authorizes every posted conjecture |
| `falsify: strike X<N>` | 2 or 3 | At Gate 2: `struck-pre-run`. At Gate 3 on a contest: see `sustain` |
| `falsify: sustain X<N>` | 3 | Contest upheld; experiment `struck-wrong-spec` |
| `falsify: overrule X<N>` | 3 | Contest rejected; Advocate must produce a remedy |
| `falsify: accept-risk S<N> <reason>` | 3 | Security finding accepted with a documented reason |
| `falsify: rollback` | 4 | Runs the rollback job |
| `falsify: deny` | 4 | Motion recorded and denied; incident closed |

Every directive is only honored when its author holds **Maintainer** or above
on the project. The certificate job re-checks the role at certification time,
not at comment time.

## Gate 1 — approve claims (issue)

The Plan flow comments with the issue's acceptance criteria rewritten as
numbered, versioned falsifiable claims (`C1`…`Cn`, `claims v1`), plus a list
of criteria it bounced as unfalsifiable, each with the one question it needs
answered to become testable.

The human edits if needed, then posts `falsify: claims approved v1`.

The certificate job later verifies:
- that comment's author holds Maintainer
- the version matches the claims the experiments actually targeted

A label (`falsify::claims-approved`) is applied **for visibility only.** It
carries no authority — no label-change trigger is documented, so nothing in
this design reads a label as an authorization.

## Gate 2 — authorize experiments (MR, Trial flow pause)

The flow pauses at a Human Input component after posting five conjectures.
Each conjecture carries:

- the claim or diff hunk it targets
- the experiment it will write
- an estimated runtime in seconds

The human approves all, or strikes any by number.

**What this authorizes:** a bounded operation — write up to five pytest files
under `.falsify/experiments/` on the scratch branch, and run them in the
sandboxed job. It is *not* an approval of code that does not yet exist. The
exact files are reviewable afterward by their digests in the certificate, and
the human can still strike any at Gate 3.

Striking here is recorded as `struck-pre-run`.

## Gate 3 — rule per finding (MR, Trial flow pause)

For each functional refutation or contract failure, the Advocate posts either:

- a **remedy** — a GitLab suggestion on the exact lines in the diff
  (suggestions can only change lines already in the diff and cannot create a
  file, which is why promotion is a separate job), or
- a **contest** — the experiment encodes the wrong spec, with reasoning.

The flow pauses. The human does one of:

| Action | Meaning |
| --- | --- |
| Apply the suggestion | Remedy accepted |
| `falsify: sustain X3` | Experiment struck, counted as `struck-wrong-spec` |
| `falsify: overrule X3` | Advocate must produce a remedy instead |

### Resolution rules

- A **remedy-accepted** finding is resolved only when *both*: the experiment
  reruns green on the new head, **and** the human has run `promote` so the
  file is present at the head with its recorded hash.
- A **sustained contest** is resolved by the ruling alone. No promotion.
- The original failing evidence stays in the record. It is never overwritten
  by the later PASS.

Security findings resolve the same way: a remedy, or a documented
`falsify: accept-risk` ruling.

### Why the flow starts a new pipeline here

A CI job does not change its result when someone replies to a thread. So the
Trial flow starts a new MR pipeline after rulings are posted, and the
certificate job on *that* pipeline reads the rulings and recomputes.

## Gate 4 — approve production, rule on the motion

Before this gate the human has already run the manual `deploy-staging` job on
the MR and seen the `live-experiments` result (a functional replay of the
conjectures over HTTP, once per feature flag state). Staging findings inform
the merge decision rather than surprising anyone later.

After merge, the main pipeline:
1. verifies the certificate against the merge commit (`certificate-verify`)
2. builds and records the image digest
3. offers `deploy-prod`

`deploy-prod` sits behind GitLab's **native deployment approval** on the
protected production environment, followed by the human **starting** the job.
Approval alone does not start it.

After the deploy, `prod-watch`:
- verifies the running revision's image digest matches the one in `events.md`
- samples error rate and p95 latency for ten minutes while replaying the MR's
  conjectures at production-like rate

The human then mentions the Monitor flow's service account on the MR. The flow
reads the `prod-watch` artifact and files **at most one** operational motion as
a GitLab incident, linked to the MR and its certificate.

The human replies `falsify: rollback` (runs the rollback job) or
`falsify: deny` (recorded; incident closed).

**A motion is an observation in a window, not proof the MR caused it.** The
incident text says so.

## What invalidates an authorization

An authorization is bound to the exact things it covered.

| Change | Invalidates |
| --- | --- |
| New MR head | Gate 2, and any unpromoted Gate 3 rulings |
| New claims version | Gate 2 |
| Changed experiment digest | The ruling on that experiment |
| Re-run of the same digests against a new head | Nothing — permitted without a new Gate 2 |

The certificate job fails if no valid Gate 2 authorization exists for the
current head and claims version.

## The Assisted claim

Four judgment gates, plus smaller human actions around them: applying
suggestions, running `promote`, running `deploy-staging`, approving and
starting production, mentioning Monitor, handling rollback.

The Assisted claim rests on two facts rather than on the count:

1. Every agent action is bounded by a human authorization that names exactly
   what it covers.
2. Only deterministic CI — tests, scans, build, certificate — runs without one.

Whether that reading of "approve every step" satisfies the organizers is their
call. This project argues it; it does not assume it.
