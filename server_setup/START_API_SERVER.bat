@echo off
REM ========================================================================
REM PREDICTIVE MAINTENANCE API SERVER - STARTUP SCRIPT
REM ========================================================================
REM This script starts the FastAPI server for the Predictive Maintenance
REM system. It loads all AI models and starts the API on port 8000.
REM ========================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo STARTING PREDICTIVE MAINTENANCE API SERVER
echo ========================================================================
echo.
echo This window will remain open while the server runs.
echo.
echo WHAT TO EXPECT:
echo   1. Model loading messages (CIA1, NASA, CWRU, Induction, Current Sig, Thermal)
echo   2. "Application startup complete" message
echo   3. Server ready to accept requests on http://localhost:8000
echo.
echo HOW TO TEST:
echo   - Open a NEW terminal/PowerShell window
echo   - Go to: server_testing\api_tests\
echo   - Run: python test_all_models.py
echo.
echo TO STOP THE SERVER: Press Ctrl+C
echo ========================================================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at .venv
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/3] Starting Python process...
echo.

REM Start the FastAPI server
echo [2/3] Loading models and starting API server...
echo.

cd ..
.venv\Scripts\python.exe -m uvicorn backend.app.main:app ^
    --host 0.0.0.0 ^
    --port 8000 ^
    --reload-delay 0.5

echo.
echo ========================================================================
echo SERVER SHUTDOWN
echo ========================================================================
pause
