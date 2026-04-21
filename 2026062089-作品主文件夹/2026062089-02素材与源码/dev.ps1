$ErrorActionPreference = 'Stop'

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $rootDir 'backend\\flask-backend'
$frontendDir = Join-Path $rootDir 'frontend'

$backendPython = Join-Path $backendDir '.venv\\Scripts\\python.exe'
if (-not (Test-Path $backendPython)) {
    $backendPython = 'python'
}

$backendCommand = "Set-Location '$backendDir'; & '$backendPython' run.py"
$frontendCommand = "Set-Location '$frontendDir'; npm run dev"

Write-Host "Starting backend in a new PowerShell window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    $backendCommand
)

Write-Host "Starting frontend in a new PowerShell window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    $frontendCommand
)

Write-Host ""
Write-Host "Backend:  http://localhost:8083" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "If backend fails, check whether backend/flask-backend/.venv exists or python is on PATH." -ForegroundColor Yellow
