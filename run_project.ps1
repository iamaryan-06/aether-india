# =====================================================================
# AETHER INDIA — Autonomous AI Business Operations Agent Launcher
# Final Year Major Project: 4-Agent LangGraph E-Commerce System
# =====================================================================

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  AETHER INDIA // 4-Agent LangGraph AI System" -ForegroundColor White
Write-Host "  Starting FastAPI Backend & Next.js Frontend..." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

$baseDir = $PSScriptRoot
$backendDir = Join-Path $baseDir "backend"
$frontendDir = Join-Path $baseDir "frontend"

# 1. Detect Python Executable (prefer local venv if available)
$venvPython = Join-Path $backendDir "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "[Info] Using virtual environment Python: $venvPython" -ForegroundColor DarkGray
} else {
    $pythonExe = "python"
}

# 1. Start FastAPI Backend on Port 8000
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8000 --reload" -WorkingDirectory $backendDir -PassThru

Start-Sleep -Seconds 2

# 2. Start Next.js Frontend on Port 3000
Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory $frontendDir -PassThru

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  Project Running!" -ForegroundColor Green
Write-Host "  Customer Storefront : http://localhost:3000" -ForegroundColor White
Write-Host "  Admin Operations    : http://localhost:3000/admin" -ForegroundColor White
Write-Host "  FastAPI Swagger Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "`nDemo Credentials:" -ForegroundColor Yellow
Write-Host "  Customer: aarav@customer.com   / Demo@1234" -ForegroundColor White
Write-Host "  Admin   : admin@aether.in      / Demo@1234" -ForegroundColor White
Write-Host "`nPress Ctrl+C to terminate both servers when finished.`n" -ForegroundColor Gray

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "Stopping servers..." -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
}
