import time

from ui.auth.token_mint import mint_backend_token
from ui.config import settings

import base64
import hashlib
import hmac
import json


def _decode(token: str, secret: str) -> dict:
    body, sig_b64 = token.split(".", 1)
    pad = "=" * (-len(sig_b64) % 4)
    got = base64.urlsafe_b64decode(sig_b64 + pad)
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    assert hmac.compare_digest(expected, got)
    pad_b = "=" * (-len(body) % 4)
    return json.loads(base64.urlsafe_b64decode(body + pad_b))


def test_mint_shape_and_claims() -> None:
    token = mint_backend_token("user-1", "a@b.c", is_admin=True)
    assert isinstance(token, str)
    assert token.count(".") == 1
    claims = _decode(token, settings.authjwt_secret)
    assert claims["sub"] == "user-1"
    assert claims["email"] == "a@b.c"
    assert claims["is_admin"] is True
    assert claims["exp"] > claims["iat"]


def test_mint_verifies_with_shared_secret() -> None:
    token = mint_backend_token("user-2", "x@y.z", is_admin=False)
    claims = _decode(token, settings.authjwt_secret)
    assert claims["sub"] == "user-2"


def test_wrong_secret_fails() -> None:
    token = mint_backend_token("user-3", "n@o.p")
    try:
        _decode(token, settings.authjwt_secret + "-wrong")
        ok = True
    except AssertionError:
        ok = False
    assert ok is False
