# Start Backend Server
Write-Host "Starting Department Ease Backend..." -ForegroundColor Green

# Check MongoDB
$mongo = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
if ($mongo.Status -ne 'Running') {
    Write-Host "MongoDB is not running. Attempting to start..." -ForegroundColor Yellow
    Start-Service -Name MongoDB
    Start-Sleep -Seconds 2
}

# Run Backend
cd backend
if (Test-Path "venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
    python main.py
}
else {
    Write-Host "Virtual environment not found! Please run setup first." -ForegroundColor Red
    Pause
}
