"""
API Key Management Endpoints

Provides endpoints for:
- Generating API keys (with password)
- Revoking API keys
- Listing users (admin only)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.auth.api_key import (
    create_api_key,
    revoke_api_key,
    list_all_users,
    verify_api_key
)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class KeyRequest(BaseModel):
    username: str
    password: str


class KeyResponse(BaseModel):
    api_key: str
    username: str
    created_at: str
    message: str


@router.post("/generate", response_model=KeyResponse)
async def generate_key(request: KeyRequest):
    """
    Generate or regenerate API key
    
    **Authentication**: Username + Password
    
    **Usage**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/api-keys/generate \\
      -H "Content-Type: application/json" \\
      -d '{"username": "admin", "password": "<YOUR_ADMIN_PASSWORD>"}'
    ```
    
    **Response**:
    ```json
    {
      "api_key": "sk_admin_abc123...",
      "username": "admin",
      "created_at": "2024-01-01T12:00:00",
      "message": "Keep this key safe! You'll need it for all API requests."
    }
    ```
    
    **Credentials**: Set via ADMIN_PASSWORD / ENGINEER_PASSWORD environment variables.
    No default passwords are accepted.
    """
    return create_api_key(request.username, request.password)


@router.post("/revoke")
async def revoke_key(request: KeyRequest):
    """
    Revoke your API key
    
    **Authentication**: Username + Password
    
    **Usage**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/api-keys/revoke \\
      -H "Content-Type: application/json" \\
      -d '{"username": "admin", "password": "<YOUR_ADMIN_PASSWORD>"}'
    ```
    """
    return revoke_api_key(request.username, request.password)


@router.get("/users")
async def get_users(current_user: dict = Depends(verify_api_key)):
    """
    List all users (requires valid API key)
    
    **Authentication**: API Key
    
    **Usage**:
    ```bash
    curl http://localhost:8000/api/v1/api-keys/users \\
      -H "X-API-Key: sk_admin_abc123..."
    ```
    """
    return {
        "users": list_all_users(),
        "requested_by": current_user["username"]
    }


@router.get("/test")
async def test_key(current_user: dict = Depends(verify_api_key)):
    """
    Test your API key
    
    **Authentication**: API Key
    
    **Usage**:
    ```bash
    curl http://localhost:8000/api/v1/api-keys/test \\
      -H "X-API-Key: sk_admin_abc123..."
    ```
    """
    return {
        "status": "success",
        "message": "API key is valid",
        "user": {
            "username": current_user["username"],
            "email": current_user.get("email"),
            "full_name": current_user.get("full_name")
        }
    }
