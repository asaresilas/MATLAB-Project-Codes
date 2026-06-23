@echo off
chcp 65001 >nul 2>&1
title MotorGuard Digital Twin

set "ROOT=%~dp0"

echo.
echo  MotorGuard Digital Twin  —  Starting servers
echo  ============================================================
echo   BACKEND  (cyan)   http://127.0.0.1:8000
echo   FRONTEND (green)  http://localhost:5173
echo.
echo   Wait for BACKEND to print "Application startup complete"
echo   then open:  http://localhost:5173
echo.
echo   Login:  admin / admin123
echo   Press Ctrl+C to stop both servers.
echo  ============================================================
echo.

cd /d "%ROOT%"
npm start
