#!/bin/bash
# lightning_setup.sh
# Run this ONCE inside Lightning AI Studio terminal to set up MotorGuard backend.
# Paste the whole block into the terminal and press Enter.

set -e
echo "========================================"
echo "  MotorGuard — Lightning AI Setup"
echo "========================================"

# ── 1. Clone the GitHub repo ──────────────────────────────────────────────────
echo "[1/5] Cloning GitHub repo..."
cd /teamspace/studios/this_studio
if [ -d "MATLAB-Project-Codes" ]; then
    echo "  Repo already exists — pulling latest..."
    cd MATLAB-Project-Codes && git pull && cd ..
else
    git clone https://github.com/asaresilas/MATLAB-Project-Codes.git
fi

# ── 2. Install Python dependencies ───────────────────────────────────────────
echo "[2/5] Installing Python dependencies..."
cd /teamspace/studios/this_studio/MATLAB-Project-Codes/backend
pip install -q -r requirements.txt

# ── 3. Create .env file for secrets ──────────────────────────────────────────
echo "[3/5] Creating .env file..."
cat > /teamspace/studios/this_studio/MATLAB-Project-Codes/backend/.env << 'ENVEOF'
HOST=0.0.0.0
PORT=8000
JWT_SECRET_KEY=motorguard2026securekey12345678
ADMIN_USERNAME=admin
ADMIN_PASSWORD=MotorGuard2026!
ENGINEER_USERNAME=engineer
ENGINEER_PASSWORD=Engineer2026!
CORS_ORIGINS=https://motorguard-asaresilas.vercel.app,http://localhost:5173
ENVEOF
echo "  .env created — edit passwords if needed."

# ── 4. Create Trained_models folder (user uploads models here) ───────────────
echo "[4/5] Creating Trained_models directory..."
mkdir -p /teamspace/studios/this_studio/MATLAB-Project-Codes/Trained_models
echo "  Upload your Trained_models/ files here using the Studio file browser."

# ── 5. Done ───────────────────────────────────────────────────────────────────
echo "[5/5] Setup complete!"
echo ""
echo "  Next: Upload your Trained_models/ folder in the file browser"
echo "  Then run:  bash lightning_start.sh"
echo ""
