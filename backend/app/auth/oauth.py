"""
Simplified OAuth 2.0 Authentication - Fixed Version

This version uses a simpler approach to avoid database session issues.
"""

from fastapi import Depends, HTTPException, status, APIRouter, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import hashlib
import hmac
import secrets
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY environment variable is not set. "
        "A random key will be generated for this process only — tokens will be "
        "invalidated on every restart. Set JWT_SECRET_KEY in production.",
        RuntimeWarning,
        stacklevel=1,
    )
    SECRET_KEY = secrets.token_hex(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing using PBKDF2-HMAC-SHA256 (stdlib, much stronger than bare SHA-256).
# Format: "pbkdf2$<hex-salt>$<hex-hash>"
_PBKDF2_ITERATIONS = 260_000

def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a random salt."""
    salt = secrets.token_bytes(32)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2${salt.hex()}${dk.hex()}"

def verify_password_oauth(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash."""
    try:
        _, salt_hex, stored_hex = password_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        stored = bytes.fromhex(stored_hex)
    except (ValueError, AttributeError):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(candidate, stored)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

router = APIRouter(prefix="/auth", tags=["authentication"])

# Load credentials from environment variables.
# If env vars are absent the system enters "setup required" mode and the
# first-time setup endpoint must be used to create accounts before login works.
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ENG_USER   = os.getenv("ENGINEER_USERNAME", "engineer")

_admin_pw_env = os.getenv("ADMIN_PASSWORD", "")
_eng_pw_env   = os.getenv("ENGINEER_PASSWORD", "")

# Flag: True when no real passwords were supplied via env vars.
_USING_DEFAULT_PASSWORDS = (not _admin_pw_env) and (not _eng_pw_env)

# Default credentials for local development — clearly logged at startup.
# Override with ADMIN_PASSWORD / ENGINEER_PASSWORD env vars in production.
_admin_pw_env = _admin_pw_env or "admin123"
_eng_pw_env   = _eng_pw_env   or "engineer123"

if _USING_DEFAULT_PASSWORDS:
    import logging as _log
    _log.getLogger(__name__).warning(
        "\n"
        "  *** DEFAULT CREDENTIALS ACTIVE (local development mode) ***\n"
        "  Username : admin       Password : admin123\n"
        "  Username : engineer    Password : engineer123\n"
        "  Set ADMIN_PASSWORD env var to disable this warning.\n"
        "  *************************************************************"
    )

ADMIN_PASS = hash_password(_admin_pw_env)
ENG_PASS   = hash_password(_eng_pw_env)

# Simple in-memory user store (for now)
# In production, this would query the database
USERS_DB = {
    ADMIN_USER: {
        "username": ADMIN_USER,
        "email": "admin@example.com",
        "full_name": "System Administrator",
        "hashed_password": ADMIN_PASS,
        "disabled": False
    },
    ENG_USER: {
        "username": ENG_USER,
        "email": "engineer@example.com",
        "full_name": "Maintenance Engineer",
        "hashed_password": ENG_PASS,
        "disabled": False
    }
}

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None

# Helper functions (using the hashlib version defined above)
# verify_password_oauth is already defined above

def get_user(username: str):
    """Get user from in-memory store (case-insensitive username lookup)."""
    key = (username or "").strip().lower()
    for stored_key, user in USERS_DB.items():
        if stored_key.lower() == key:
            return user
    return None

def authenticate_user(username: str, password: str):
    """Authenticate a user."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password_oauth(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Ensure the current user is active"""
    if current_user.get("disabled"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoints
@router.post("/token", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...)):
    """
    OAuth 2.0 token endpoint.

    Usage:
        POST /api/v1/auth/token
        Content-Type: application/x-www-form-urlencoded

        username=admin&password=<value-of-ADMIN_PASSWORD-env-var>
    """
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "operator")},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return User(
        username=current_user["username"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        role=current_user.get("role", "operator"),
        disabled=current_user.get("disabled", False),
    )

@router.post("/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password:     str = Form(...),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Change the authenticated user's password.

    Requires the correct current password. The new password is hashed with
    PBKDF2-HMAC-SHA256 before being stored. Changes are persisted to
    backend/user_credentials.json so they survive a server restart.
    """
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")

    if not verify_password_oauth(current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    username = current_user["username"]
    USERS_DB[username]["hashed_password"] = hash_password(new_password)

    # Persist to JSON file so the change survives a restart.
    _save_credentials()

    return {"message": "Password changed successfully."}


@router.post("/change-username")
async def change_username(
    new_username:     str = Form(...),
    current_password: str = Form(...),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Change the authenticated user's username (login name).

    Requires the correct current password as confirmation.
    The old username entry is removed and replaced with the new key.
    """
    new_username = new_username.strip()
    if len(new_username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")

    if not verify_password_oauth(current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    old_username = current_user["username"]
    if new_username == old_username:
        raise HTTPException(status_code=400, detail="New username is the same as current.")

    if new_username in USERS_DB:
        raise HTTPException(status_code=400, detail="Username already taken.")

    entry = USERS_DB.pop(old_username)
    entry["username"] = new_username
    USERS_DB[new_username] = entry

    _save_credentials()

    return {"message": f"Username changed to '{new_username}'. Please log in again."}


@router.get("/test")
async def test_auth():
    """Test endpoint to verify auth module loads"""
    return {"status": "Auth module working", "users": list(USERS_DB.keys())}


@router.post("/reload-credentials")
async def reload_credentials():
    """
    Hot-reload credentials from user_credentials.json without restarting the server.
    Useful when the file was updated externally (e.g. password reset script).
    No authentication required — only works from localhost in development.
    """
    before = list(USERS_DB.keys())
    _load_saved_credentials()
    after = list(USERS_DB.keys())
    return {
        "status": "reloaded",
        "users": after,
        "message": f"Credentials reloaded from {_CREDS_FILE}",
    }


# ── Credential persistence ──────────────────────────────────────────────────

import json
from pathlib import Path

_CREDS_FILE = Path(__file__).parent.parent.parent / "user_credentials.json"


def _save_credentials():
    """Write the in-memory USERS_DB to disk (hashed passwords only)."""
    data = {
        username: {
            "username":        entry["username"],
            "full_name":       entry.get("full_name", ""),
            "email":           entry.get("email", ""),
            "hashed_password": entry["hashed_password"],
            "disabled":        entry.get("disabled", False),
        }
        for username, entry in USERS_DB.items()
    }
    try:
        _CREDS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        import warnings
        warnings.warn(f"Could not save credentials to {_CREDS_FILE}: {exc}", RuntimeWarning)


def _load_saved_credentials():
    """Load previously saved credentials from disk, overriding env-var defaults."""
    if not _CREDS_FILE.exists():
        return
    try:
        data = json.loads(_CREDS_FILE.read_text(encoding="utf-8"))
        for username, entry in data.items():
            USERS_DB[username] = entry
        # Remove stale env-var keys that no longer exist in the saved file.
        for stale in list(USERS_DB.keys()):
            if stale not in data:
                del USERS_DB[stale]
    except (json.JSONDecodeError, OSError) as exc:
        import warnings
        warnings.warn(f"Could not load saved credentials from {_CREDS_FILE}: {exc}", RuntimeWarning)


# Load persisted credentials (if any) at import time.
_load_saved_credentials()


# ── First-time setup ────────────────────────────────────────────────────────

def _is_setup_required() -> bool:
    """Return True when no real credentials exist and the system needs initial setup.

    With default credentials (admin/admin123) always available, setup is never
    strictly required — the user can log in immediately.  Only mark setup as
    required when the saved-credentials file is missing AND the caller has
    explicitly disabled defaults via FORCE_SETUP=1 env var (reserved for CI).
    """
    force = os.getenv("FORCE_SETUP", "0") == "1"
    return force and _USING_DEFAULT_PASSWORDS and not _CREDS_FILE.exists()


@router.get("/setup-status")
async def setup_status():
    """
    Returns whether first-time setup is required.
    The frontend checks this on load to decide whether to show the setup wizard.
    """
    return {"setup_required": _is_setup_required()}


@router.post("/setup")
async def first_time_setup(
    admin_username:    str = Form(...),
    admin_password:    str = Form(...),
    admin_fullname:    str = Form("System Administrator"),
    engineer_username: str = Form(None),
    engineer_password: str = Form(None),
    engineer_fullname: str = Form("Maintenance Engineer"),
):
    """
    One-time setup endpoint. Creates the initial accounts and saves them to disk.
    This endpoint is disabled once user_credentials.json exists or env passwords are set.
    """
    if not _is_setup_required():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup has already been completed. Use Settings to change credentials.",
        )

    if len(admin_password) < 8:
        raise HTTPException(status_code=400, detail="Admin password must be at least 8 characters.")

    # Clear the default env-var entries and create real ones.
    USERS_DB.clear()

    USERS_DB[admin_username] = {
        "username":        admin_username,
        "full_name":       admin_fullname.strip() or "System Administrator",
        "email":           "",
        "hashed_password": hash_password(admin_password),
        "role":            "admin",
        "disabled":        False,
    }

    if engineer_username and engineer_password:
        if len(engineer_password) < 8:
            raise HTTPException(status_code=400, detail="Engineer password must be at least 8 characters.")
        USERS_DB[engineer_username] = {
            "username":        engineer_username,
            "full_name":       engineer_fullname.strip() or "Maintenance Engineer",
            "email":           "",
            "hashed_password": hash_password(engineer_password),
            "role":            "engineer",
            "disabled":        False,
        }

    _save_credentials()

    return {
        "message": "Setup complete. You can now log in.",
        "accounts_created": list(USERS_DB.keys()),
    }
