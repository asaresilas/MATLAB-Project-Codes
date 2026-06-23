"""
API Key Authentication
======================
Issues API keys after verifying credentials against the single USERS_DB
that is owned and persisted by oauth.py.  No second user store is maintained
here — all credential changes (password / username) go through oauth.py and
are immediately visible to API-key auth because both modules share the same dict.
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
import secrets
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# ── Shared user store (owned by oauth.py) ─────────────────────────────────────
# Import the live reference — mutations in oauth.py (change-password, setup…)
# are immediately reflected here because Python dicts are mutable references.
from app.auth.oauth import USERS_DB, verify_password_oauth   # noqa: E402

# ── API key header ─────────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ── In-memory key store: api_key → username ────────────────────────────────────
# Cleared on restart (stateless token model — users re-request keys after restart).
API_KEYS_DB: Dict[str, str] = {}


# ── Key generation ─────────────────────────────────────────────────────────────

def generate_api_key(username: str) -> str:
    return f"sk_{username}_{secrets.token_urlsafe(32)}"


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Verify credentials against the shared oauth USERS_DB."""
    user = USERS_DB.get(username)
    if not user or user.get("disabled"):
        return None
    # oauth.py stores the hash under "hashed_password"
    if not verify_password_oauth(password, user.get("hashed_password", "")):
        return None
    return user


def create_api_key(username: str, password: str) -> dict:
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Revoke old key if one exists
    old_key = user.get("api_key")
    if old_key and old_key in API_KEYS_DB:
        del API_KEYS_DB[old_key]

    api_key = generate_api_key(username)
    user["api_key"] = api_key
    user["key_created_at"] = datetime.utcnow().isoformat()
    API_KEYS_DB[api_key] = username
    logger.info("API key issued for user '%s'", username)

    return {
        "api_key": api_key,
        "username": username,
        "created_at": user["key_created_at"],
        "message": "Keep this key safe — it grants full API access.",
    }


def get_user_from_api_key(api_key: str) -> Optional[dict]:
    username = API_KEYS_DB.get(api_key)
    if not username:
        return None
    user = USERS_DB.get(username)
    if not user or user.get("disabled"):
        return None
    return user


async def verify_api_key(api_key: str = Security(api_key_header)) -> dict:
    """
    FastAPI dependency — validates the X-API-Key header.

    Usage:
        @router.get("/protected")
        async def protected(user: dict = Depends(verify_api_key)):
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Add the 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    user = get_user_from_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return user


def revoke_api_key(username: str, password: str) -> dict:
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    api_key = user.get("api_key")
    if api_key and api_key in API_KEYS_DB:
        del API_KEYS_DB[api_key]
    user["api_key"] = None
    user["key_created_at"] = None
    logger.info("API key revoked for user '%s'", username)
    return {"message": "API key revoked successfully"}


def list_all_users() -> list:
    return [
        {
            "username": u["username"],
            "email": u.get("email"),
            "full_name": u.get("full_name"),
            "has_api_key": u.get("api_key") is not None,
            "key_created_at": u.get("key_created_at"),
            "disabled": u.get("disabled", False),
        }
        for u in USERS_DB.values()
    ]
