"""Configuration. Nothing here is a literal secret, by design.

Control 5 in docs/controls.md: no stored cloud credentials anywhere in this
project. The API token is read from the environment; the dev default is
explicitly marked as a dev default and is refused when FALSIFY_ENV is not
"dev".
"""
from __future__ import annotations

import os
from dataclasses import dataclass

DEV_TOKEN = "dev-token-not-a-secret"


@dataclass(frozen=True)
class Settings:
    env: str
    api_token: str
    database_url: str
    gpa_minimum: float
    country_allowlist: tuple[str, ...]
    default_page_size: int
    max_page_size: int

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"


def _require_token(env: str) -> str:
    token = os.environ.get("FALSIFY_API_TOKEN")
    if token:
        return token
    if env == "dev":
        return DEV_TOKEN
    raise RuntimeError(
        "FALSIFY_API_TOKEN is required outside dev. "
        "No token literal is committed to this repository."
    )


def load_settings() -> Settings:
    env = os.environ.get("FALSIFY_ENV", "dev")
    return Settings(
        env=env,
        api_token=_require_token(env),
        database_url=os.environ.get("FALSIFY_DB", "falsify.db"),
        # Claim thresholds. These are spec, not tuning knobs — an experiment
        # that disagrees with one of these is testing the spec.
        gpa_minimum=2.5,
        country_allowlist=("US", "KE", "IN", "NG", "BR", "PH"),
        default_page_size=20,
        max_page_size=100,
    )


settings = load_settings()
