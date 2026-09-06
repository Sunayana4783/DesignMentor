# Start backend and frontend in separate terminals for local development
$root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting DesignMentor AI in development mode..." -ForegroundColor Cyan

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\backend'; .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "Backend  -> http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend -> http://localhost:3000" -ForegroundColor Green
