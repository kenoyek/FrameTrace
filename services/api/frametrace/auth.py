"""Supabase asymmetric signing keys only. Never trust client decoded claims."""

import threading
import time
from functools import lru_cache
from urllib.parse import urlparse
from uuid import UUID

import jwt
from fastapi import HTTPException

from .config import settings


class BoundedJWKClient(jwt.PyJWKClient):
    """Unknown key IDs cannot force an unbounded number of remote JWKS fetches."""

    def __init__(self, url):
        super().__init__(url, lifespan=300, timeout=5)
        self._fetch_lock = threading.Lock()
        self._attempted = float("-inf")
        self._previous = None

    def fetch_data(self):
        with self._fetch_lock:
            if time.monotonic() - self._attempted < 30:
                if self._previous is not None:
                    return self._previous
                raise jwt.PyJWKClientConnectionError("JWKS refresh is cooling down")
            self._attempted = time.monotonic()
            self._previous = None
            self._previous = super().fetch_data()
            return self._previous


@lru_cache(maxsize=4)
def jwks_client(url: str):
    return BoundedJWKClient(url + "/auth/v1/.well-known/jwks.json")


def identity(authorization: str | None, required: bool = True) -> str | None:
    if authorization is None and not required:
        return None
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in to continue.", headers={"WWW-Authenticate": "Bearer"})
    url = (settings.supabase_url or "").rstrip("/")
    parsed = urlparse(url)
    if (
        not url
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise HTTPException(503, "Account authentication is not configured.")
    token = authorization[7:]
    if len(token) > 16384:
        raise HTTPException(401, "Invalid session.")
    try:
        key = jwks_client(url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=url + "/auth/v1",
            options={"require": ["sub", "exp", "iat", "aud", "iss"]},
        )
        if claims.get("role") != "authenticated":
            raise jwt.InvalidTokenError("Not a user session")
        return str(UUID(claims["sub"]))
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(503, "Session verification is temporarily unavailable.") from None
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(
            401, "Session expired or invalid.", headers={"WWW-Authenticate": "Bearer"}
        ) from None
