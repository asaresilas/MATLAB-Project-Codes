@echo off
echo ================================================================================
echo STARTING API SERVER
echo ================================================================================
echo.
echo This window will stay open while the server runs.
echo Wait for "Application startup complete" message.
echo.
echo Then open a NEW terminal and run:
echo   .venv\Scripts\python.exe tests\test_api_key_auth.py
echo.
echo Press Ctrl+C to stop the server
echo ================================================================================
echo.

.venv\Scripts\python.exe run_server.py

pause
