"""Parser for the `falsify:` comment syntax.

Deliberately strict. An authorization is read from GitLab identity and
structured state, never from a model deciding whether a comment sounded like
approval. An unrecognized `falsify:` line is an error, not a guess — a typo
in an authorization must fail loudly rather than silently not authorize.

Every directive is honored only when its author holds Maintainer or above.
The role is re-checked at certification time, not at comment time.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

MAINTAINER_ACCESS_LEVEL = 40


class Directive(StrEnum):
    CLAIMS_APPROVED = "claims-approved"
    APPROVE_ALL = "approve-all"
    STRIKE = "strike"
    SUSTAIN = "sustain"
    OVERRULE = "overrule"
    ACCEPT_RISK = "accept-risk"
    ROLLBACK = "rollback"
    DENY = "deny"


PATTERNS: list[tuple[re.Pattern[str], Directive]] = [
    (re.compile(r"^falsify: claims approved (?P<version>v\d+)$"), Directive.CLAIMS_APPROVED),
    (re.compile(r"^falsify: approve all$"), Directive.APPROVE_ALL),
    (re.compile(r"^falsify: strike (?P<target>X\d+)$"), Directive.STRIKE),
    (re.compile(r"^falsify: sustain (?P<target>X\d+)$"), Directive.SUSTAIN),
    (re.compile(r"^falsify: overrule (?P<target>X\d+)$"), Directive.OVERRULE),
    (re.compile(r"^falsify: accept-risk (?P<target>S\d+) (?P<reason>.+)$"), Directive.ACCEPT_RISK),
    (re.compile(r"^falsify: rollback$"), Directive.ROLLBACK),
    (re.compile(r"^falsify: deny$"), Directive.DENY),
]

_LOOKS_LIKE_DIRECTIVE = re.compile(r"^falsify:", re.IGNORECASE)


class MalformedDirective(ValueError):
    """A line starting with `falsify:` that matched no known directive."""


class InsufficientRole(PermissionError):
    """The comment author does not hold Maintainer or above."""


@dataclass(frozen=True)
class Ruling:
    directive: Directive
    target: str | None
    version: str | None
    reason: str | None
    author_username: str
    author_access_level: int
    comment_id: str
    created_at: str

    @property
    def authorized(self) -> bool:
        return self.author_access_level >= MAINTAINER_ACCESS_LEVEL


def parse_line(line: str) -> tuple[Directive, dict[str, str]] | None:
    """Parse one comment line.

    Returns None for a line that is not a directive at all. Raises
    MalformedDirective for a line that tried to be one and failed — a near
    miss must not be silently ignored.
    """
    stripped = line.strip()
    if not _LOOKS_LIKE_DIRECTIVE.match(stripped):
        return None

    for pattern, directive in PATTERNS:
        match = pattern.match(stripped)
        if match:
            return directive, match.groupdict()

    raise MalformedDirective(
        f"line starts with 'falsify:' but matched no directive: {stripped!r}. "
        "Syntax is exact and case-sensitive; see docs/gates.md."
    )


def parse_comment(
    body: str,
    *,
    author_username: str,
    author_access_level: int,
    comment_id: str,
    created_at: str,
) -> list[Ruling]:
    """Parse every directive in a comment body.

    Unauthorized rulings are returned with `authorized == False` rather than
    dropped, so the certificate can record the attempt.
    """
    rulings: list[Ruling] = []
    for line in body.splitlines():
        parsed = parse_line(line)
        if parsed is None:
            continue
        directive, groups = parsed
        rulings.append(
            Ruling(
                directive=directive,
                target=groups.get("target"),
                version=groups.get("version"),
                reason=groups.get("reason"),
                author_username=author_username,
                author_access_level=author_access_level,
                comment_id=comment_id,
                created_at=created_at,
            )
        )
    return rulings
