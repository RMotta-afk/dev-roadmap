from datetime import UTC, datetime, timedelta

from jose import jwt

from ui.config import settings


def mint_backend_token(
    user_id: str,
    email: str,
    *,
    is_admin: bool = False,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.authjwt_secret, algorithm="HS256")
