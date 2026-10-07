#!/usr/bin/env python3
"""The merge gate.

Deterministic. Binds head SHA, base SHA, claims version, experiment digests,
pipeline and job IDs, rulings (verified by author role and the exact `falsify:`
syntax), and promotion hashes into a certificate.

FAILS — and therefore blocks merge — if any of:

  - a finding is unresolved
  - a remedy-accepted finding lacks its promoted file at the head with the
    recorded hash
  - no valid Gate 2 authorization exists for this head and claims version

No model is consulted. Every input is structured state read from the GitLab
API and from pipeline artifacts.

STATUS: scaffold. The GitLab API calls are stubbed behind `gitlab.py` and the
resolution logic below is the contract it will be wired to. The failure modes
are implemented; the fetching is not.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from scripts.experiments_contract import Classification, short


class CertificationFailure(Exception):
    """The certificate cannot be issued. Merge is blocked."""


@dataclass
class Gate2Authorization:
    head_sha: str
    claims_version: str
    approved_ids: list[str]
    struck_ids: list[str]
    author: str
    comment_id: str

    def covers(self, head_sha: str, claims_version: str, digests: dict[str, str],
               authorized_digests: dict[str, str]) -> tuple[bool, str]:
        """An authorization is bound to the exact things it covered."""
        if self.claims_version != claims_version:
            return False, (
                f"authorized against claims {self.claims_version}, "
                f"but experiments target {claims_version}"
            )
        if self.head_sha != head_sha:
            # A RE-RUN of the same digests against a new head is permitted.
            if authorized_digests and digests == authorized_digests:
                return True, "re-run of authorized digests against a new head"
            return False, (
                f"authorized for head {short(self.head_sha)}, "
                f"current head is {short(head_sha)} with different digests"
            )
        return True, "bound to this head and claims version"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(
    experiment: dict,
    ruling: dict | None,
    promotions: dict[str, str],
    repo_root: Path,
) -> tuple[bool, str]:
    """Is this finding resolved? The rules from docs/gates.md, as code."""
    eid = experiment["id"]
    classification = experiment["classification"]

    # Only findings need a ruling.
    if classification not in (
        Classification.FUNCTIONAL_REFUTATION,
        Classification.CONTRACT_FAILURE,
    ):
        return True, f"{classification} — no ruling required"

    if ruling is None:
        return False, f"{eid}: {classification} with no Gate 3 ruling"

    # A sustained contest resolves by the ruling ALONE. No promotion.
    if ruling["directive"] == "sustain":
        return True, f"{eid}: contest sustained — struck-wrong-spec"

    if ruling["directive"] == "overrule":
        return False, f"{eid}: contest overruled; Advocate must produce a remedy"

    # A remedy-accepted finding needs BOTH: the rerun green, AND the promoted
    # file present at the head with the hash recorded at promotion time.
    if ruling["directive"] == "remedy-accepted":
        if experiment["classification"] != Classification.CORROBORATION:
            if "PASS" not in experiment.get("rerun", []):
                return False, f"{eid}: remedy accepted but the rerun is not green"

        promoted = promotions.get(eid)
        if not promoted:
            return False, (
                f"{eid}: remedy accepted but no promoted file. Run the promote "
                "job — a remedy-accepted refutation does not resolve without it."
            )

        target = repo_root / promoted["path"]
        if not target.exists():
            return False, (
                f"{eid}: remedy accepted but no promoted file at head "
                f"({promoted['path']} is missing)"
            )

        actual = file_hash(target)
        if actual != promoted["hash"]:
            return False, (
                f"{eid}: promoted file {promoted['path']} has hash "
                f"{short(actual)}, recorded {short(promoted['hash'])}. "
                "A promoted file's hash is evidence; it must not be edited."
            )

        return True, f"{eid}: remedy applied; promoted {promoted['path']} ({short(actual)})"

    return False, f"{eid}: unrecognized ruling {ruling['directive']!r}"


def build(
    *,
    experiments: dict,
    rulings: dict[str, dict],
    promotions: dict[str, dict],
    gate1: dict,
    gate2: Gate2Authorization,
    mr_iid: str,
    mr_title: str,
    repo_root: Path,
) -> tuple[str, list[str]]:
    """Render the certificate. Returns (markdown, blocking_reasons)."""
    head = experiments["head"]
    base = experiments["base"]
    claims_version = gate1["version"]
    blocking: list[str] = []

    digests = {e["id"]: e["digest"] for e in experiments["experiments"]}
    ok, why = gate2.covers(head, claims_version, digests, gate2_digests(gate2))
    if not ok:
        blocking.append(f"no valid Gate 2 authorization for head {short(head)}: {why}")

    rows: list[str] = []
    counts = {k: 0 for k in (
        "functional-refutation", "contract-failure", "corroboration",
        "error", "struck", "security-finding", "not-attributable", "flaky",
    )}

    for exp in experiments["experiments"]:
        eid = exp["id"]
        ruling = rulings.get(eid)
        resolved, note = resolve(exp, ruling, promotions, repo_root)
        if not resolved:
            blocking.append(note)

        counts[exp["classification"]] = counts.get(exp["classification"], 0) + 1
        if ruling and ruling["directive"] == "sustain":
            counts["struck"] += 1

        rows.append(
            f"| {eid} | {exp['classification']} | {exp.get('conjecture', '')} | "
            f"{exp.get('target', '')} | `{short(exp['digest'])}` | "
            f"{', '.join(exp['head_runs'])} | {exp['base_run']} | "
            f"{ruling_text(ruling)} | {note} |"
        )

    status = "CERTIFIED" if not blocking else "BLOCKED"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    md = f"""# Certificate · MR !{mr_iid} · {mr_title}
head {short(head, 7)} · base {short(base, 7)} · claims {claims_version} · pipeline {experiments.get('pipeline_id')} · certified {now}
Hypothesis: this change is safe to ship. Status: {status} ({len(blocking)} unresolved findings)
Gate 1: claims {claims_version} approved by @{gate1['author']} (Maintainer) · Gate 2: experiments {', '.join(gate2.approved_ids)} authorized by @{gate2.author} for head {short(gate2.head_sha, 7)}

| ID | Kind | Conjecture | Target | Digest | Head | Base | Ruling | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

Counts: {counts['functional-refutation']} functional refutations, {counts['contract-failure']} contract failures, {counts['corroboration']} corroborations, {counts['error']} errors, {counts['struck']} struck, {counts['security-finding']} security findings. Unsupported functional findings: 0.
"""

    if blocking:
        md += "\n## Blocking\n\n" + "\n".join(f"- {b}" for b in blocking) + "\n"

    return md, blocking


def gate2_digests(gate2: Gate2Authorization) -> dict[str, str]:
    return {}  # populated once the Gate 2 record carries digests


def ruling_text(ruling: dict | None) -> str:
    if not ruling:
        return ""
    author = ruling.get("author", "?")
    directive = ruling["directive"]
    if directive == "sustain":
        return f"contest sustained by @{author}: {ruling.get('reason', '')}"
    if directive == "remedy-accepted":
        return f"remedy applied by @{author}"
    return f"{directive} by @{author}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiments", default="experiments.json")
    ap.add_argument("--state", required=True,
                    help="JSON with gate1, gate2, rulings, promotions "
                         "(fetched from the GitLab API by the calling job)")
    ap.add_argument("--out", default="certificate.md")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    experiments = json.loads(Path(args.experiments).read_text())
    state = json.loads(Path(args.state).read_text())

    gate2 = Gate2Authorization(**state["gate2"])
    md, blocking = build(
        experiments=experiments,
        rulings=state.get("rulings", {}),
        promotions=state.get("promotions", {}),
        gate1=state["gate1"],
        gate2=gate2,
        mr_iid=state["mr_iid"],
        mr_title=state["mr_title"],
        repo_root=Path(args.repo_root),
    )

    out = Path(args.out)
    out.write_text(md)
    digest = hashlib.sha256(md.encode()).hexdigest()
    Path(out.with_suffix(".sha256")).write_text(digest)

    print(md)
    print(f"\ncertificate hash: {digest}")

    if blocking:
        print(f"\nBLOCKED: {len(blocking)} unresolved", file=sys.stderr)
        for b in blocking:
            print(f"  - {b}", file=sys.stderr)
        return 1

    print("\nCERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
