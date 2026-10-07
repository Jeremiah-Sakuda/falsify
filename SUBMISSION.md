# Submission checklist

Devpost, Life After Code. **Form submitted by end of day Oct 26** — the Oct 27
9:00am EDT close is not a working window.

- Path: **A (Start Fresh)**
- Autonomy level: **Assisted**
- Opt **out** of the Environmental prize — no sustainability claim is made
- Prize targets: Best Assisted Agent (Path A); plus Most Stages Covered or
  Most Creative, at the judges' discretion

## Required

- [ ] Public GitLab project under the hackathon group, MIT LICENSE detected
      and shown in the About section
- [ ] First commit dated **on or after Oct 5, 2026** (the proof of eligibility)
- [ ] Visible CI/CD pipeline history showing `experiments`, `certificate`,
      `promote`, `build`, `deploy-staging`, `live-experiments`, an approved
      `deploy-prod`, and `prod-watch` runs
- [ ] `README.md` — the one rule, the vocabulary table, how to run the flows
- [ ] `.gitlab/duo/flows/plan.yaml`, `trial.yaml`, `monitor.yaml` in the repo
      (subject to MIT and the GitLab DCO per the rules)
- [ ] `ledger/` with entries from all 14 evaluation MRs, plus the generated
      `LEDGER.md` index
- [ ] `deploy/` with the Cloud Run code; the **production URL** (min instances
      1, landing page at `/`) in the form for the Google Cloud bonus
- [ ] Production service stays live through the winners' announcement
      (around Nov 16, 2026)
- [ ] Demo video under 3:00 on YouTube, public, captions on, no trademarks or
      licensed music
- [ ] Text description: what it does, the problem, who it is for, how GitLab
      automates the post-code lifecycle, the evaluation table, and the
      complement-to-Duo framing

## Devpost fields, drafted in advance

**Tagline:** No red test, no accusation.

**Summary (150 words):** _draft before Oct 24_

**How we built it:** names, by name — custom flows, triggers, the Human Input
component, security scanning templates, protected environments, deployment
approvals, Feature Flags (Unleash), and the observability stack.

**Challenges:** tells the wrong-spec story truthfully. Falsify was wrong N
times; here are the experiments that were struck.

## Prize framing in the description

- **Best Assisted Agent** — the Path prize. Argued on the two facts in
  `docs/gates.md`: every agent action is bounded by a human authorization that
  names exactly what it covers, and only deterministic CI runs without one.
- **Most Stages Covered** — argued with the nine-stage table. Every stage is
  touched by something that does real work, not a placeholder job.
- **Most Creative** — argued with the one rule.

The judges choose. Each project may win one Path prize and one special prize.
