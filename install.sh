#!/bin/bash
# Localized Voting System - Installation Script for macOS/Linux

echo ""
echo "============================================================"
echo "  FEZA VOTING SYSTEM - LOCAL INSTALLATION (macOS/Linux)"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3 using your package manager:"
    echo "  - macOS (Homebrew): brew install python3"
    echo "  - Ubuntu/Debian: sudo apt-get install python3-pip"
    exit 1
fi

echo "[1/5] Python found:"
python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi
echo ""

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
echo ""

# Install requirements
echo "[4/5] Installing Python dependencies..."
pip install Flask==3.0.0 flask-cors==4.0.0
if [ $? -ne 0 ]; then
    echo "[WARNING] Some packages may have failed to install"
fi
echo ""

# Make scripts executable
chmod +x start_server.sh

echo "[5/5] Installation complete!"
echo ""
echo "============================================================"
echo "   INSTALLATION SUCCESSFUL"
echo "============================================================"
echo ""
echo "To start the voting system:"
echo ""
echo "1. Run: ./start_server.sh"
echo "   (or run manually: source venv/bin/activate && python app_local.py)"
echo ""
echo "2. Once running, access from any computer:"
echo "   - Main voting page: http://[SERVER-IP]:3000"
echo "   - Registration page: http://[SERVER-IP]:3000/register.html"
echo "   - System info: http://[SERVER-IP]:3000/api/system-info"
echo ""
echo "============================================================"
echo ""
