"""Mint short-lived HMAC access tokens for the API (stdlib only)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from ui.config import settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def mint_backend_token(
    user_id: str,
    email: str,
    *,
    is_admin: bool = False,
) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": str(email),
        "is_admin": bool(is_admin),
        "iat": now,
        "exp": now + int(settings.jwt_expiry_minutes) * 60,
    }
    secret = settings.authjwt_secret
    body = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    sig = hmac.new(
        secret.encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).digest()
    token = f"{body}.{_b64url(sig)}"
    # Local UI log — compare secret_len/suffix with docker compose logs -f api
    print(
        f"[ui.auth] minted token len={len(token)} "
        f"secret_len={len(secret)} suffix=...{secret[-4:] if len(secret) >= 4 else secret}",
        flush=True,
    )
    return token
