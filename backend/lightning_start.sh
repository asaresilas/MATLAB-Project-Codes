#!/bin/bash
# lightning_start.sh
# Run this every time you want to start the MotorGuard backend on Lightning AI.
# The Studio gives you a public HTTPS URL automatically on port 8000.

echo "========================================"
echo "  MotorGuard — Starting Backend"
echo "========================================"

cd /teamspace/studios/this_studio/MATLAB-Project-Codes/backend

# Load .env variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "  Environment variables loaded."
fi

# Check models exist
MODEL_COUNT=$(find ../Trained_models -name "*.keras" 2>/dev/null | wc -l)
if [ "$MODEL_COUNT" -eq 0 ]; then
    echo ""
    echo "  WARNING: No .keras model files found in Trained_models/"
    echo "  Upload your Trained_models/ folder first using the file browser."
    echo "  The backend will start but predictions will return 503."
    echo ""
fi

echo "  Starting FastAPI backend on port 8000..."
echo "  Click 'View App' in Lightning AI to get your public URL."
echo ""

python run.py
