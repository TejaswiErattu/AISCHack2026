#!/bin/bash
# TerraLend — Combined startup script
# Launches backend (FastAPI) and frontend (Vite) together
# Usage: ./start.sh

set -e

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "All processes stopped."
}

trap cleanup EXIT INT TERM

# Start backend
echo "Starting backend on :8000..."
cd "$(dirname "$0")"
python3 -m uvicorn backend.main:app --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 20); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend ready!"
        break
    fi
    sleep 0.5
done

# Start frontend
echo "Starting frontend on :5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "TerraLend is running:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both."

wait
