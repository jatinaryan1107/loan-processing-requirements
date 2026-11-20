[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8000,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$exitCode = 0
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw 'Python environment missing. Run: python -m venv .venv; then .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt'
    }
    & $pythonPath -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
    if ($LASTEXITCODE -ne 0) {
        throw 'Python 3.11 or newer is required. Recreate the virtual environment with a supported Python version.'
    }
    & $pythonPath -c 'import fastapi, uvicorn, dotenv, multipart, docx, pypdf, httpx'
    if ($LASTEXITCODE -ne 0) {
        throw 'Python dependencies are incomplete. Run: .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt'
    }
    if (-not (Test-Path -LiteralPath 'frontend\dist\index.html' -PathType Leaf)) {
        throw 'Built interface missing. Run: cd frontend; npm.cmd ci; npm.cmd run build; cd ..'
    }
    Write-Host "Local workspace: http://127.0.0.1:$Port"
    if ($Check) {
        Write-Host 'Startup checks passed. The server was not started.'
    } else {
        Write-Host 'Press Ctrl+C to stop. Saved projects remain in the configured SQLite database.'
        & $pythonPath -m uvicorn backend.app:app --host 127.0.0.1 --port $Port
        $exitCode = $LASTEXITCODE
    }
} catch {
    Write-Host "Cannot start workspace: $($_.Exception.Message)" -ForegroundColor Red
    $exitCode = 1
} finally {
    Pop-Location
}
exit $exitCode

