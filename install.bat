@echo off
REM Localized Voting System - Installation Script for Windows
REM This script sets up the voting system on any Windows computer

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   FEZA VOTING SYSTEM - LOCAL INSTALLATION
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install requirements
echo [4/5] Installing Python dependencies...
pip install Flask==3.0.0 flask-cors==4.0.0
if errorlevel 1 (
    echo [WARNING] Some packages may have failed to install, but system may still work
)
echo.

REM Complete
echo [5/5] Installation complete!
echo.
echo ============================================================
echo   INSTALLATION SUCCESSFUL
echo ============================================================
echo.
echo To start the voting system:
echo.
echo 1. Run: start_server.bat
echo    (or run this manually: venv\Scripts\activate.bat ^& python app_local.py)
echo.
echo 2. Once running, access from any computer:
echo    - Main voting page: http://[SERVER-IP]:3000
echo    - Registration page: http://[SERVER-IP]:3000/register.html
echo    - System info: http://[SERVER-IP]:3000/api/system-info
echo.
echo ============================================================
echo.
pause
