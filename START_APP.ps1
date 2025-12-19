# Scooter API Startup Script (PowerShell)
# Right-click and select "Run with PowerShell" or run: .\START_APP.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Scooter Rental API - Startup Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if MongoDB is running
Write-Host "[1/3] Checking MongoDB status..." -ForegroundColor Yellow
$mongoService = Get-Service -Name MongoDB -ErrorAction SilentlyContinue

if ($null -eq $mongoService) {
    Write-Host "ERROR: MongoDB service not found!" -ForegroundColor Red
    Write-Host "Please install MongoDB from: https://www.mongodb.com/try/download/community" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if ($mongoService.Status -ne "Running") {
    Write-Host "MongoDB is not running. Starting MongoDB..." -ForegroundColor Yellow
    try {
        Start-Service -Name MongoDB
        Write-Host "MongoDB started successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: Failed to start MongoDB!" -ForegroundColor Red
        Write-Host "Try running this script as Administrator" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
else {
    Write-Host "MongoDB is already running!" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] Checking Python dependencies..." -ForegroundColor Yellow
$pythonPath = ".\venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please ensure you're in the correct directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python environment found!" -ForegroundColor Green

Write-Host ""
Write-Host "[3/3] Starting Scooter API server..." -ForegroundColor Yellow
Write-Host "Server will start on: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the Flask application
& $pythonPath app.py

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"


