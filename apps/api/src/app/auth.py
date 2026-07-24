from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from app.config import settings


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Decode and verify the HS256 Bearer JWT (minted by Streamlit UI)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.authjwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_iss": False},
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    email = payload.get("email")
    if user_id is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user_id,
        "email": email,
        "is_admin": payload.get("is_admin", False),
    }


# Reusable dependency alias for route injection
require_auth = get_current_user


# ---------------------------------------------------------------------------
# Example usage (commented out — drop into a router when ready)
# ---------------------------------------------------------------------------
# from fastapi import APIRouter, Depends
# router = APIRouter()
#
# @router.get("/protected")
# async def protected(user=Depends(require_auth)):
#     return {"user_id": user["user_id"]}
