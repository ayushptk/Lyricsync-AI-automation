$ErrorActionPreference = "Stop"

Write-Host "Setting up YTSaaS Local Development Environment..." -ForegroundColor Cyan

# Ensure script is running from the 'scripts' directory or adjust paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# 1. Check for .env file
if (-not (Test-Path "..\.env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item "..\.env.example" "..\.env"
} else {
    Write-Host ".env file already exists." -ForegroundColor Green
}

# 2. Check Docker is running (basic check)
Write-Host "Checking if Docker is running..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running."
    }
    Write-Host "Docker is running." -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# 3. Build and run containers
Write-Host "Building and starting Docker containers..." -ForegroundColor Cyan
Set-Location ..
docker-compose up -d --build

Write-Host "------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "Frontend (Next.js): http://localhost:3000"
Write-Host "Backend API (FastAPI): http://localhost:8000/docs"
Write-Host "Flower (Celery Monitor): http://localhost:5555"
Write-Host "------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Run 'docker-compose logs -f' from the root directory to view logs." -ForegroundColor Yellow
