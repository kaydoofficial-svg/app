@echo off
title Class Recorder — MP4 to Telegram

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python from https://python.org
    pause
    exit /b
)

echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting server...
echo Open http://localhost:5050 in your browser
echo.
start "" "http://localhost:5050/index.html"
python server.py

pause
