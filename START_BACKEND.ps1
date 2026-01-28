# Backend Startup Script for Windows PowerShell
# Run this script to start the backend server

Write-Host "Starting Backend Server..." -ForegroundColor Green

# Navigate to backend directory
$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path "$backendDir\backend")) {
    $backendDir = "$backendDir\backend"
} else {
    $backendDir = "$backendDir\backend"
}
Set-Location $backendDir

Write-Host "Current directory: $backendDir" -ForegroundColor Yellow

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Cyan
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Check if FastAPI is installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$fastapiInstalled = & "venv\Scripts\python.exe" -c "import fastapi; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: FastAPI not installed!" -ForegroundColor Red
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & "venv\Scripts\pip.exe" install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

# Check if port 8000 is available
$port = 8000
$portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "WARNING: Port $port is already in use!" -ForegroundColor Yellow
    Write-Host "Trying port 8010..." -ForegroundColor Yellow
    $port = 8010
    $portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "ERROR: Port 8010 is also in use!" -ForegroundColor Red
        Write-Host "Please free up a port or specify a different one." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting server on port $port..." -ForegroundColor Green
Write-Host "Server will be available at: http://127.0.0.1:$port" -ForegroundColor Cyan
Write-Host "API docs available at: http://127.0.0.1:$port/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
& "venv\Scripts\uvicorn.exe" app.main:app --reload --host 127.0.0.1 --port $port
