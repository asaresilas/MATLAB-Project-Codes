---
title: MotorGuard Backend API
emoji: ⚙️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# MotorGuard — FastAPI Backend

Multi-modal predictive maintenance AI for squirrel-cage induction motors.

## Endpoints

- `GET  /health` — health check
- `GET  /docs`   — interactive API documentation (Swagger UI)
- `POST /api/v1/predict/simulink` — full multi-modal prediction (MATLAB HTTP fallback)
- `WS   /ws/dashboard` — live dashboard WebSocket (frontend)
- `WS   /ws/simulink/{client_id}` — MATLAB WebSocket connection

## Environment Variables (set as Secrets in HF Spaces)

| Variable | Required | Description |
|---|---|---|
| `HF_MODEL_REPO` | Yes | HF Hub model repo, e.g. `your-username/motorguard-models` |
| `JWT_SECRET_KEY` | Yes | 32-char random string for JWT signing |
| `ADMIN_PASSWORD` | Yes | Admin user password |
| `ENGINEER_PASSWORD` | Yes | Engineer user password |
| `CORS_ORIGINS` | Yes | Comma-separated allowed frontend origins |

## MATLAB Connection

Point `api_wrapper.m` at this Space URL for HTTP mode:

```matlab
setenv('MOTORGUARD_SERVER', 'https://your-username-motorguard.hf.space')
```
