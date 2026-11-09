#!/usr/bin/env bash
# ==============================================================================
# AegisPay 1-Click Demo Launcher (Bash / macOS / Linux)
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "================================================================="
echo "       AegisPay - Autonomous Escrow & Settlement Engine         "
echo "================================================================="

if [ ! -f ".env" ]; then
    echo "[!] .env not found. Copying from .env.example..."
    cp .env.example .env
    echo "[✓] Created .env (Running in graceful PayPal mock fallback mode)"
fi

echo ""
echo "[1/3] Running AegisPay verification test suite..."
python3 backend/tests/test_pipeline.py

echo ""
echo "[2/3] Starting FastAPI Backend on http://localhost:8000..."
(cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

echo ""
echo "[3/3] Starting Next.js Frontend on http://localhost:3000..."
PKG_MGR="npm"
if command -v pnpm &> /dev/null; then
    PKG_MGR="pnpm"
fi

(cd frontend && $PKG_MGR run dev) &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "================================================================="
echo "  AegisPay is live!"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend Docs: http://localhost:8000/docs"
echo "================================================================="
echo "Press Ctrl+C to stop."

wait
