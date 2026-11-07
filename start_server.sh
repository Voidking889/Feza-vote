#!/bin/bash
# Voting System Server Start Script for macOS/Linux

set -e

if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run install.sh first"
    exit 1
fi

echo ""
echo "============================================================"
echo "   FEZA VOTING SYSTEM - STARTING SERVER"
echo "============================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "[SERVER] Starting Gunicorn server..."
gunicorn --workers 4 --bind 0.0.0.0:3000 app:app

