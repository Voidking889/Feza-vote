@echo off
REM Voting System Server Start Script
REM This script starts the localized voting server

setlocal enabledelayedexpansion

if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INITIALIZING VOTING SYSTEM......
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the server
echo [INFO] Starting voting server...
echo.
python app.py

pause
