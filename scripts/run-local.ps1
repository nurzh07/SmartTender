# SmartTender — Docker жоқ/local режим (тек PostgreSQL+Redis Docker-да)
# Алдымен: Docker Desktop іске қосылған болсын, содан:
#   docker compose up -d smarttender_db smarttender_redis

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    (Get-Content ".env") -replace "smarttender_db", "localhost" -replace "smarttender_redis", "localhost" |
        Set-Content ".env.localhost"
    Write-Host "Created .env — for local API use localhost URLs in DATABASE_URL and REDIS_URL"
}

$env:DATABASE_URL = "postgresql://smarttender:smarttender_pass@localhost:5432/smarttender"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:SECRET_KEY = "dev-secret-key"
$env:ALGORITHM = "HS256"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "15"
$env:REFRESH_TOKEN_EXPIRE_DAYS = "30"

if (-not (Test-Path "venv\Scripts\python.exe")) {
    python -m venv venv
}
& .\venv\Scripts\pip install -q -r requirements.txt
& .\venv\Scripts\alembic upgrade head
& .\venv\Scripts\python scripts\seed.py
Write-Host "API: http://localhost:8000/docs"
& .\venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
