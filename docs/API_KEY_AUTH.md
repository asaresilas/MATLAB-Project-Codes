# API Key Authentication System

## Quick Start Guide

### Step 1: Generate Your API Key

Login with your username and password to get an API key:

```bash
curl -X POST http://localhost:8000/api/v1/api-keys/generate \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Response:**
```json
{
  "api_key": "sk_admin_abc123xyz456...",
  "username": "admin",
  "created_at": "2024-01-01T12:00:00",
  "message": "Keep this key safe! You'll need it for all API requests."
}
```

### Step 2: Use Your API Key

Include the API key in the `X-API-Key` header for all requests:

```bash
curl http://localhost:8000/api/v1/models \
  -H "X-API-Key: sk_admin_abc123xyz456..."
```

### Step 3: Make Predictions

```bash
curl -X POST http://localhost:8000/api/v1/predict/cia1 \
  -H "X-API-Key: sk_admin_abc123xyz456..." \
  -H "Content-Type: application/json" \
  -d '{"signal": [0.1, 0.2, ...]}'
```

---

## Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| engineer | engineer123 | Maintenance Engineer |
| demo | demo123 | Demo User |

---

## Python Example

```python
import requests

# Step 1: Get API key
response = requests.post(
    "http://localhost:8000/api/v1/api-keys/generate",
    json={"username": "admin", "password": "admin123"}
)
api_key = response.json()["api_key"]

# Step 2: Use API key for predictions
headers = {"X-API-Key": api_key}

# List models
models = requests.get(
    "http://localhost:8000/api/v1/models",
    headers=headers
).json()

# Make prediction
prediction = requests.post(
    "http://localhost:8000/api/v1/predict/cia1",
    headers=headers,
    json={"signal": [0.1, 0.2, ...]}
).json()
```

---

## API Key Management

### Test Your Key
```bash
curl http://localhost:8000/api/v1/api-keys/test \
  -H "X-API-Key: your-key-here"
```

### Revoke Your Key
```bash
curl -X POST http://localhost:8000/api/v1/api-keys/revoke \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### List All Users
```bash
curl http://localhost:8000/api/v1/api-keys/users \
  -H "X-API-Key: your-key-here"
```

---

## Security Notes

1. **Keep your API key secret** - Never commit it to version control
2. **Regenerate if compromised** - Use the generate endpoint to create a new key
3. **Use HTTPS in production** - Never send keys over unencrypted connections
4. **Change default passwords** - Update the passwords in `backend/app/auth/api_key.py`

---

## Testing

Run the automated test:
```bash
.venv\Scripts\python.exe tests/test_api_key_auth.py
```

This will:
1. Generate an API key
2. Test the key validity
3. List available models
4. Make a test prediction
