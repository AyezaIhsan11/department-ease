# Start Frontend Application
Write-Host "Starting Department Ease Frontend..." -ForegroundColor Green

cd frontend
$env:NODE_OPTIONS = "--max-old-space-size=4096"
npm run dev
