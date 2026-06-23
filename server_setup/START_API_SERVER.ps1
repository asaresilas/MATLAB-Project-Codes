# ========================================================================
# PREDICTIVE MAINTENANCE API SERVER - STARTUP SCRIPT (PowerShell)
# ========================================================================
# This script starts the FastAPI server for the Predictive Maintenance
# system. It loads all AI models and starts the API on port 8002.
# ========================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "STARTING PREDICTIVE MAINTENANCE API SERVER" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This window will remain open while the server runs." -ForegroundColor Yellow
Write-Host ""
Write-Host "WHAT TO EXPECT:" -ForegroundColor Green
Write-Host "  1. Model loading messages (CIA1, NASA, CWRU, Induction, Current Sig, Thermal)" -ForegroundColor White
Write-Host "  2. 'Application startup complete' message" -ForegroundColor White
Write-Host "  3. Server ready to accept requests on http://localhost:8002" -ForegroundColor White
Write-Host ""
Write-Host "HOW TO TEST:" -ForegroundColor Green
Write-Host "  - Open a NEW PowerShell window" -ForegroundColor White
Write-Host "  - Go to: server_testing\api_tests\" -ForegroundColor White
Write-Host "  - Run: python test_all_models.py" -ForegroundColor White
Write-Host ""
Write-Host "TO STOP THE SERVER: Press Ctrl+C" -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "Please run the following commands:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor White
    Write-Host "  .venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] Virtual environment found" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Loading models and starting API server..." -ForegroundColor Green
Write-Host ""

# Change to parent directory (project root)
Push-Location ..

# Start the FastAPI server
& .venv\Scripts\python.exe -m uvicorn backend.app.main:app `
    --host 0.0.0.0 `
    --port 8002 `
    --reload-delay 0.5

Pop-Location

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "SERVER SHUTDOWN" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Read-Host "Press Enter to close this window"
