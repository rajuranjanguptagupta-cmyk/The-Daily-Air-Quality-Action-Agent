@echo off
title AirGuard AI
echo.
echo  ==========================================
echo    AirGuard AI - Starting Server...
echo  ==========================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo  ERROR: venv not found. Run setup first.
    pause
    exit /b 1
)

echo  Groq AI Connected: qwen/qwen3.8-27b
echo  Server starting at: http://localhost:5000
echo.
echo  Press Ctrl+C to stop the server.
echo  ==========================================
echo.

venv\Scripts\python.exe run.py

pause
