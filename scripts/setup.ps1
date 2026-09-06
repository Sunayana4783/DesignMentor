$ErrorActionPreference = "Stop"
$root = "C:\Users\sunay\OneDrive\Desktop\Learn_agent\designmentor-ai"

Write-Host ""
Write-Host "=== DesignMentor AI Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check .env
if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
    Write-Host "[1] Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "    -> Open .env and set OPENAI_API_KEY and SECRET_KEY before continuing" -ForegroundColor Red
    exit 0
} else {
    Write-Host "[1] .env already exists" -ForegroundColor Green
}

# 2. Start Docker services
Write-Host ""
Write-Host "[2] Starting Docker services..." -ForegroundColor Cyan
Set-Location $root
docker compose up -d postgres redis
Start-Sleep -Seconds 6

# 3. Backend Python setup
Write-Host ""
Write-Host "[3] Setting up Python backend..." -ForegroundColor Cyan
Set-Location "$root\backend"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "    -> Created .venv" -ForegroundColor Green
}

& "$root\backend\.venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Host "    -> Dependencies installed" -ForegroundColor Green

# 4. Run migrations
Write-Host ""
Write-Host "[4] Running database migrations..." -ForegroundColor Cyan
$env:DATABASE_URL = "postgresql+asyncpg://designmentor:designmentor_secret@localhost:5432/designmentor_db"
& "$root\backend\.venv\Scripts\alembic.exe" upgrade head
Write-Host "    -> Migrations done" -ForegroundColor Green

# 5. Seed curriculum
Write-Host ""
Write-Host "[5] Seeding curriculum..." -ForegroundColor Cyan
& "$root\backend\.venv\Scripts\python.exe" -m app.curriculum.seeder
Write-Host "    -> Curriculum seeded" -ForegroundColor Green

# 6. Train RF model
Write-Host ""
Write-Host "[6] Training Random Forest model..." -ForegroundColor Cyan
& "$root\backend\.venv\Scripts\python.exe" -m app.ml.test_rf_model
Write-Host "    -> Model trained" -ForegroundColor Green

# 7. Frontend
Write-Host ""
Write-Host "[7] Installing frontend dependencies..." -ForegroundColor Cyan
Set-Location "$root\frontend"
npm install
Write-Host "    -> Frontend ready" -ForegroundColor Green

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Start backend:  cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload" -ForegroundColor Yellow
Write-Host "Start frontend: cd frontend && npm run dev" -ForegroundColor Yellow
Write-Host ""
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
