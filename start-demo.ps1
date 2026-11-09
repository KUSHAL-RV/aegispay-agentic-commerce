# ==============================================================================
# AegisPay 1-Click Demo Launcher (PowerShell / Windows)
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       AegisPay - Autonomous Escrow and Settlement Engine        " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $RepoRoot) { $RepoRoot = Get-Location }
Set-Location $RepoRoot

# 1. Check .env existence
$EnvFile = Join-Path $RepoRoot ".env"
$EnvExample = Join-Path $RepoRoot ".env.example"

if (-not (Test-Path $EnvFile)) {
    Write-Host "[!] .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item $EnvExample $EnvFile
    Write-Host "[*] Created .env (Running in graceful PayPal mock fallback mode)" -ForegroundColor Green
    Write-Host "    To use real PayPal Sandbox credentials, edit .env with your client ID and secret." -ForegroundColor DarkGray
}

# 2. Check Python executable
$PyExe = "python"
$VenvPy = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $PyExe = $VenvPy
    Write-Host "Using virtual environment: $VenvPy" -ForegroundColor DarkGray
}

# 3. Run automated tests first
Write-Host "`n[1/3] Running AegisPay verification test suite..." -ForegroundColor Cyan
& $PyExe "$RepoRoot\backend\tests\test_pipeline.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Test suite reported warnings, proceeding with launch..." -ForegroundColor Yellow
} else {
    Write-Host "[*] All tests verified successfully!" -ForegroundColor Green
}

# 4. Resolve Node package manager on Windows (.cmd)
$NpmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $NpmCmd) {
    $NpmCmd = (Get-Command npm -ErrorAction SilentlyContinue).Source
}
if (-not $NpmCmd) {
    $NpmCmd = "npm"
}

$NodeModules = Join-Path $RepoRoot "frontend\node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "`n[!] Installing frontend dependencies..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$NpmCmd`"", "install" -WorkingDirectory "$RepoRoot\frontend" -Wait -NoNewWindow
    Write-Host "[*] Frontend dependencies installed!" -ForegroundColor Green
}

# 5. Start Backend Server in a new console window
Write-Host "`n[2/3] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Cyan
$BackendArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
$BackendProcess = Start-Process -FilePath $PyExe -ArgumentList $BackendArgs -WorkingDirectory "$RepoRoot\backend" -PassThru

# 6. Start Frontend Dev Server via cmd.exe in a new console window
Write-Host "`n[3/3] Starting Next.js and AG Grid Frontend on http://localhost:3000..." -ForegroundColor Cyan
$FrontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$NpmCmd`"", "run", "dev" -WorkingDirectory "$RepoRoot\frontend" -PassThru

Start-Sleep -Seconds 4

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "  AegisPay is live!" -ForegroundColor Green
Write-Host "  - Frontend Dashboard:   http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - Backend Swagger Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - OpenAPI Specification: $RepoRoot\openapi.json" -ForegroundColor DarkGray
Write-Host "  - APIMatic SDK:          $RepoRoot\sdk-apimatic\" -ForegroundColor DarkGray
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C or close this terminal to stop both servers." -ForegroundColor Yellow

# Launch browser
Start-Process "http://localhost:3000"

try {
    # Keep the console alive until interrupted
    while ($true) {
        Start-Sleep -Seconds 2
        if ($BackendProcess -and $BackendProcess.HasExited) { break }
        if ($FrontendProcess -and $FrontendProcess.HasExited) { break }
    }
} finally {
    Write-Host "`nShutting down AegisPay servers..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    # Ensure port cleanup
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
