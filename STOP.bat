@echo off
chcp 65001 >nul 2>&1
title MotorGuard Shutdown

echo.
echo  Stopping MotorGuard servers...
echo.

:: ── Kill backend (python on port 8000) ───────────────────────────────────────
echo  Stopping backend (port 8000)...
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr " :8000 "') do (
    if not "%%P"=="0" (
        taskkill /F /PID %%P >nul 2>&1
        echo    Stopped PID %%P
    )
)

:: ── Kill frontend (node on port 5173) ────────────────────────────────────────
echo  Stopping frontend (port 5173)...
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr " :5173 "') do (
    if not "%%P"=="0" (
        taskkill /F /PID %%P >nul 2>&1
        echo    Stopped PID %%P
    )
)

echo.
echo  All servers stopped.
echo.
pause
