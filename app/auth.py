"""Bearer token auth on write endpoints.

Token comparison is constant-time. `==` on a secret is a timing oracle, not a
style preference.
"""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from app.config import settings


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    presented = authorization.removeprefix("Bearer ")
    if not hmac.compare_digest(presented, settings.api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
