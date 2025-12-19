@echo off
REM Scooter API Startup Script
REM Double-click this file to start the application

echo ============================================================
echo   Scooter Rental API - Startup Script
echo ============================================================
echo.

REM Check if MongoDB is running
echo [1/3] Checking MongoDB status...
sc query "MongoDB" | find "RUNNING" >nul
if errorlevel 1 (
    echo MongoDB is not running. Starting MongoDB...
    net start MongoDB
    if errorlevel 1 (
        echo ERROR: Failed to start MongoDB!
        echo Please start MongoDB manually or run as Administrator.
        pause
        exit /b 1
    )
    echo MongoDB started successfully!
) else (
    echo MongoDB is already running!
)

echo.
echo [2/3] Starting Scooter API server...
echo Server will start on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start the Flask application
venv\Scripts\python.exe app.py

echo.
echo Server stopped.
pause


