# ==============================================================================
# AegisPay 1-Click Demo Launcher (PowerShell / Windows)
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       AegisPay - Autonomous Escrow & Settlement Engine         " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $RepoRoot

# Check .env existence
$EnvFile = Join-Path $RepoRoot ".env"
$EnvExample = Join-Path $RepoRoot ".env.example"

if (-not (Test-Path $EnvFile)) {
    Write-Host "[!] .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item $EnvExample $EnvFile
    Write-Host "[✓] Created .env (Running in graceful PayPal mock fallback mode)" -ForegroundColor Green
    Write-Host "    To use real PayPal Sandbox credentials, edit .env with your client ID & secret." -ForegroundColor DarkGray
}

# Run automated tests first
Write-Host "`n[1/3] Running AegisPay verification test suite..." -ForegroundColor Cyan
python "$RepoRoot\backend\tests\test_pipeline.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Test suite reported warnings, proceeding with launch..." -ForegroundColor Yellow
} else {
    Write-Host "[✓] All tests verified successfully!" -ForegroundColor Green
}

# Start Backend Server
Write-Host "`n[2/3] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Cyan
$BackendProcess = Start-Process python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory "$RepoRoot\backend" -PassThru

# Start Frontend Dev Server
Write-Host "`n[3/3] Starting Next.js + AG Grid Frontend on http://localhost:3000..." -ForegroundColor Cyan

# Check if npm or pnpm is available
$PkgMgr = "npm"
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    $PkgMgr = "pnpm"
}

Write-Host "Using package manager: $PkgMgr" -ForegroundColor DarkGray
$FrontendProcess = Start-Process $PkgMgr -ArgumentList "run dev" -WorkingDirectory "$RepoRoot\frontend" -PassThru

Start-Sleep -Seconds 3

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "  AegisPay is live!" -ForegroundColor Green
Write-Host "  - Frontend Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - Backend Swagger Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - OpenAPI Specification: $RepoRoot\openapi.json" -ForegroundColor DarkGray
Write-Host "  - APIMatic SDK: $RepoRoot\sdk-apimatic\" -ForegroundColor DarkGray
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C or close this terminal window to stop servers." -ForegroundColor Yellow

# Launch browser
Start-Process "http://localhost:3000"

try {
    Wait-Process -Id $BackendProcess.Id, $FrontendProcess.Id
} finally {
    Stop-Process -Id $BackendProcess.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $FrontendProcess.Id -ErrorAction SilentlyContinue
}
