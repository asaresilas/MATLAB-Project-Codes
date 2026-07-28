@echo off
chcp 65001 >nul 2>&1
title MotorGuard Digital Twin

set "ROOT=%~dp0"

echo.
echo  MotorGuard Digital Twin  —  Starting servers (LOCAL MODE)
echo  ============================================================
echo   BACKEND   http://127.0.0.1:8000
echo   FRONTEND  http://localhost:5173
echo   API docs  http://127.0.0.1:8000/docs
echo.
echo   Wait ~30 seconds for backend models to load.
echo   MATLAB:  setenv('MOTORGUARD_SERVER','http://127.0.0.1:8000')
echo  ============================================================
echo.

:: ── Start backend in its own window ──────────────────────────────────────────
start "MotorGuard Backend" cmd /k "cd /d "%ROOT%backend" && python run.py"

:: ── Wait 5 seconds then start frontend ───────────────────────────────────────
timeout /t 5 /nobreak >nul
start "MotorGuard Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

:: ── Wait for frontend to be ready then open browser ──────────────────────────
timeout /t 8 /nobreak >nul
start http://localhost:5173

echo.
echo  Both servers started. Close the two server windows or run STOP.bat to shut down.
echo.
