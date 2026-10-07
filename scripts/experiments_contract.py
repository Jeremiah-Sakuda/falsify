"""The experiments job contract, as code.

A refutation is recorded only when ALL of the following hold:

  1. The result on the MR head is FAIL (an assertion failed) — not ERROR
     (import error, fixture error, timeout, collection error).
  2. The same FAIL reproduces on a SECOND run on the MR head.
  3. The result on the merge base is PASS, or the experiment targets a file
     that does not exist on the base (new code), recorded as `n/a`.

Anything else is a corroboration, an error, or not-attributable. This module
is the single place that decision is made, so it cannot drift between the
harness, the certificate, and the ledger.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Outcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"      # an assertion failed
    ERROR = "ERROR"    # could not run: import, fixture, timeout, collection
    NA = "n/a"         # no base version — the target file is new


class Classification(StrEnum):
    FUNCTIONAL_REFUTATION = "functional-refutation"
    CONTRACT_FAILURE = "contract-failure"
    CORROBORATION = "corroboration"
    ERROR = "error"
    NOT_ATTRIBUTABLE = "not-attributable"
    FLAKY = "flaky"


@dataclass
class ExperimentResult:
    experiment_id: str
    path: str
    digest: str
    head_runs: list[Outcome] = field(default_factory=list)
    base_run: Outcome | None = None
    target: str = ""
    conjecture: str = ""
    rewrite_attempts: int = 0

    @property
    def classification(self) -> Classification:
        return classify(self.head_runs, self.base_run)

    @property
    def is_finding(self) -> bool:
        return self.classification in (
            Classification.FUNCTIONAL_REFUTATION,
            Classification.CONTRACT_FAILURE,
        )


def classify(head_runs: list[Outcome], base_run: Outcome | None) -> Classification:
    """Apply the contract. The only place this decision is made."""
    if not head_runs:
        return Classification.ERROR

    # An ERROR anywhere on head disqualifies the experiment entirely. It is
    # not a finding of any kind.
    if Outcome.ERROR in head_runs:
        return Classification.ERROR

    # A FAIL that does not reproduce is flaky, not evidence.
    if len(set(head_runs)) > 1:
        return Classification.FLAKY

    head = head_runs[0]

    if head is Outcome.PASS:
        # A survived attempt, not proof.
        return Classification.CORROBORATION

    # head is FAIL, reproduced.
    if base_run is Outcome.NA:
        # New code with no base version. A possible violation of an approved
        # claim, NOT a regression — it does not borrow the functional
        # refutation's guarantee.
        return Classification.CONTRACT_FAILURE

    if base_run is Outcome.PASS:
        return Classification.FUNCTIONAL_REFUTATION

    if base_run is Outcome.FAIL:
        # Pre-existing. Out of scope for this MR.
        return Classification.NOT_ATTRIBUTABLE

    # base_run is ERROR or None — the base comparison did not happen, so the
    # refutation cannot be established.
    return Classification.ERROR


def digest_file(path: str | Path) -> str:
    """Content digest. The experiment's identity in the certificate.

    Byte-for-byte: a reformatted experiment is a different experiment and its
    Gate 3 ruling does not carry over.
    """
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def short(digest: str, n: int = 8) -> str:
    return digest[:n]
