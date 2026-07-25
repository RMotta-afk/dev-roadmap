import base64
import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.auth import decode_access_token, get_current_user
from app.config import settings


def _mint(secret: str, *, exp_delta: int = 900, **extra: object) -> str:
    now = int(time.time())
    payload = {
        "sub": "uid-1",
        "email": "u@example.com",
        "is_admin": False,
        "iat": now,
        "exp": now + exp_delta,
        **extra,
    }
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{body}.{sig_b64}"


def _creds(token: str) -> MagicMock:
    c = MagicMock()
    c.credentials = token
    return c


def test_decode_valid() -> None:
    token = _mint(settings.authjwt_secret, is_admin=True)
    payload = decode_access_token(token, settings.authjwt_secret)
    assert payload["sub"] == "uid-1"
    assert payload["is_admin"] is True


def test_decode_wrong_secret() -> None:
    token = _mint("other-secret")
    with pytest.raises(ValueError, match="invalid signature"):
        decode_access_token(token, settings.authjwt_secret)


def test_decode_expired() -> None:
    token = _mint(settings.authjwt_secret, exp_delta=-10)
    with pytest.raises(ValueError, match="token expired"):
        decode_access_token(token, settings.authjwt_secret)


@pytest.mark.asyncio
async def test_get_current_user_valid() -> None:
    token = _mint(settings.authjwt_secret, is_admin=True)
    user = await get_current_user(_creds(token))
    assert user == {
        "user_id": "uid-1",
        "email": "u@example.com",
        "is_admin": True,
    }


@pytest.mark.asyncio
async def test_get_current_user_missing() -> None:
    with pytest.raises(HTTPException) as ei:
        await get_current_user(None)
    assert ei.value.status_code == 401
    assert ei.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_user_bad_token() -> None:
    with pytest.raises(HTTPException) as ei:
        await get_current_user(_creds("not.a.valid.token"))
    assert ei.value.status_code == 401
