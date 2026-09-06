# Load knowledge base into pgvector (run after setup)
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\backend"
& ".venv\Scripts\Activate.ps1"
python -m app.rag.loader
Write-Host "RAG knowledge base loaded." -ForegroundColor Green
