"""Bearer token auth: HMAC-signed opaque tokens minted by the Streamlit UI."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

security = HTTPBearer(auto_error=False)


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def decode_access_token(token: str, secret: str) -> dict:
    """Validate `body.sig` HMAC token; raise ValueError on any failure."""
    try:
        body, sig_b64 = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("malformed token") from exc

    expected = hmac.new(
        secret.encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).digest()
    try:
        got = _b64url_decode(sig_b64)
    except Exception as exc:
        raise ValueError("invalid signature encoding") from exc

    if not hmac.compare_digest(expected, got):
        raise ValueError("invalid signature")

    try:
        payload = json.loads(_b64url_decode(body))
    except Exception as exc:
        raise ValueError("invalid payload") from exc

    if not isinstance(payload, dict):
        raise ValueError("invalid payload type")

    exp = payload.get("exp")
    if exp is None:
        raise ValueError("missing exp")
    if int(exp) < int(time.time()):
        raise ValueError("token expired")

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Verify the Bearer access token (minted by Streamlit UI)."""
    secret = settings.authjwt_secret
    secret_suffix = secret[-4:] if len(secret) >= 4 else secret

    if credentials is None:
        print(
            f"[app.auth] FAIL missing Bearer header "
            f"secret_len={len(secret)} suffix=...{secret_suffix}",
            flush=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials or ""
    token_preview = f"{token[:16]}...(len={len(token)})" if token else "(empty)"

    try:
        payload = decode_access_token(token, secret)
    except ValueError as exc:
        msg = str(exc)
        print(
            f"[app.auth] FAIL {msg} token={token_preview} "
            f"secret_len={len(secret)} suffix=...{secret_suffix}",
            flush=True,
        )
        detail = (
            "Token has expired"
            if msg == "token expired"
            else f"Could not validate credentials ({msg})"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    email = payload.get("email")
    if user_id is None or email is None:
        print(f"[app.auth] FAIL missing sub/email keys={list(payload)}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(
        f"[app.auth] OK user_id={user_id} email={email} "
        f"secret_len={len(secret)} suffix=...{secret_suffix}",
        flush=True,
    )
    return {
        "user_id": str(user_id),
        "email": str(email),
        "is_admin": bool(payload.get("is_admin", False)),
    }


require_auth = get_current_user
