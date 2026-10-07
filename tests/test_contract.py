"""Tests for the deterministic core.

The classification contract and the ruling parser are the two places where a
mistake would let an unsupported finding through, or let an unauthorized
comment act as an authorization. They get base-suite coverage even though the
base suite is otherwise deliberately thin.
"""
from __future__ import annotations

import pytest

from scripts.experiments_contract import (
    Classification as C,
)
from scripts.experiments_contract import (
    Outcome as O,
)
from scripts.experiments_contract import (
    classify,
)
from scripts.rulings import (
    MAINTAINER_ACCESS_LEVEL,
    Directive,
    MalformedDirective,
    parse_comment,
    parse_line,
)


class TestClassification:
    """The one rule, as a truth table."""

    def test_reproduced_fail_on_head_passing_on_base_is_a_refutation(self):
        assert classify([O.FAIL, O.FAIL], O.PASS) is C.FUNCTIONAL_REFUTATION

    def test_no_base_version_is_a_contract_failure_not_a_refutation(self):
        # New code. A possible violation of an approved claim, NOT a
        # regression — it must not borrow the refutation's guarantee.
        assert classify([O.FAIL, O.FAIL], O.NA) is C.CONTRACT_FAILURE

    def test_failing_on_base_too_is_not_attributable(self):
        assert classify([O.FAIL, O.FAIL], O.FAIL) is C.NOT_ATTRIBUTABLE

    def test_passing_on_head_is_corroboration_only(self):
        # A survived attempt, not proof.
        assert classify([O.PASS, O.PASS], O.PASS) is C.CORROBORATION

    def test_a_fail_that_does_not_reproduce_is_flaky_not_evidence(self):
        assert classify([O.FAIL, O.PASS], O.PASS) is C.FLAKY
        assert classify([O.PASS, O.FAIL], O.PASS) is C.FLAKY

    @pytest.mark.parametrize(
        "head,base",
        [
            ([O.ERROR, O.FAIL], O.PASS),
            ([O.FAIL, O.ERROR], O.PASS),
            ([O.ERROR, O.ERROR], O.PASS),
        ],
    )
    def test_an_error_on_head_is_never_a_finding(self, head, base):
        # An import, fixture, timeout, or collection error is not a finding
        # of any kind.
        assert classify(head, base) is C.ERROR

    def test_an_error_on_base_cannot_establish_a_refutation(self):
        # Without a base comparison there is no refutation to establish.
        assert classify([O.FAIL, O.FAIL], O.ERROR) is C.ERROR

    def test_a_missing_base_run_cannot_establish_a_refutation(self):
        assert classify([O.FAIL, O.FAIL], None) is C.ERROR

    def test_no_runs_at_all_is_an_error(self):
        assert classify([], O.PASS) is C.ERROR

    @pytest.mark.parametrize(
        "classification,is_finding",
        [
            (C.FUNCTIONAL_REFUTATION, True),
            (C.CONTRACT_FAILURE, True),
            (C.CORROBORATION, False),
            (C.ERROR, False),
            (C.NOT_ATTRIBUTABLE, False),
            (C.FLAKY, False),
        ],
    )
    def test_only_two_classifications_are_findings(self, classification, is_finding):
        from scripts.experiments_contract import ExperimentResult

        r = ExperimentResult(experiment_id="X1", path="x", digest="d")
        mapping = {
            C.FUNCTIONAL_REFUTATION: ([O.FAIL, O.FAIL], O.PASS),
            C.CONTRACT_FAILURE: ([O.FAIL, O.FAIL], O.NA),
            C.CORROBORATION: ([O.PASS, O.PASS], O.PASS),
            C.ERROR: ([O.ERROR], O.PASS),
            C.NOT_ATTRIBUTABLE: ([O.FAIL, O.FAIL], O.FAIL),
            C.FLAKY: ([O.FAIL, O.PASS], O.PASS),
        }
        r.head_runs, r.base_run = mapping[classification]
        assert r.is_finding is is_finding


class TestRulingSyntax:
    """Authorizations come from structured state, never from interpretation."""

    def test_claims_approval_captures_the_version(self):
        directive, groups = parse_line("falsify: claims approved v2")
        assert directive is Directive.CLAIMS_APPROVED
        assert groups["version"] == "v2"

    @pytest.mark.parametrize(
        "line,directive,target",
        [
            ("falsify: approve all", Directive.APPROVE_ALL, None),
            ("falsify: strike X3", Directive.STRIKE, "X3"),
            ("falsify: sustain X12", Directive.SUSTAIN, "X12"),
            ("falsify: overrule X1", Directive.OVERRULE, "X1"),
            ("falsify: rollback", Directive.ROLLBACK, None),
            ("falsify: deny", Directive.DENY, None),
        ],
    )
    def test_every_directive_parses(self, line, directive, target):
        got_directive, groups = parse_line(line)
        assert got_directive is directive
        assert groups.get("target") == target

    def test_accept_risk_requires_a_reason(self):
        directive, groups = parse_line("falsify: accept-risk S1 vendored, no exploit path")
        assert directive is Directive.ACCEPT_RISK
        assert groups["target"] == "S1"
        assert groups["reason"] == "vendored, no exploit path"

        with pytest.raises(MalformedDirective):
            parse_line("falsify: accept-risk S1")

    def test_an_ordinary_comment_is_not_a_directive(self):
        assert parse_line("this looks fine to me") is None
        assert parse_line("I think falsify: should approve this") is None

    @pytest.mark.parametrize(
        "line",
        [
            "falsify: approve everything",
            "falsify: claims approved",
            "falsify: claims approved 2",
            "falsify: sustain 3",
            "falsify: SUSTAIN X3",
            "falsify: strike X3 please",
        ],
    )
    def test_a_near_miss_raises_rather_than_silently_not_authorizing(self, line):
        # A typo in an authorization must fail loudly. Silently treating it as
        # "no authorization" would be indistinguishable from a real refusal.
        with pytest.raises(MalformedDirective):
            parse_line(line)

    def test_multiple_directives_in_one_comment(self):
        rulings = parse_comment(
            "reviewed these\nfalsify: sustain X3\nfalsify: overrule X4\nthanks",
            author_username="jsakuda",
            author_access_level=MAINTAINER_ACCESS_LEVEL,
            comment_id="c1",
            created_at="2026-10-15T12:00:00Z",
        )
        assert [r.directive for r in rulings] == [Directive.SUSTAIN, Directive.OVERRULE]
        assert all(r.authorized for r in rulings)

    def test_below_maintainer_is_recorded_but_not_authorized(self):
        # Returned rather than dropped, so the certificate can record the
        # attempt.
        (ruling,) = parse_comment(
            "falsify: rollback",
            author_username="drive-by",
            author_access_level=MAINTAINER_ACCESS_LEVEL - 10,
            comment_id="c2",
            created_at="2026-10-15T12:00:00Z",
        )
        assert ruling.directive is Directive.ROLLBACK
        assert ruling.authorized is False

    def test_exactly_maintainer_is_authorized(self):
        (ruling,) = parse_comment(
            "falsify: approve all",
            author_username="jsakuda",
            author_access_level=MAINTAINER_ACCESS_LEVEL,
            comment_id="c3",
            created_at="2026-10-15T12:00:00Z",
        )
        assert ruling.authorized is True
