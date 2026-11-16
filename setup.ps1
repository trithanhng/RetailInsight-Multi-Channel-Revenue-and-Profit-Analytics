$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create virtual environment' }
}
& '.\.venv\Scripts\python.exe' -m pip install --no-cache-dir -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
Write-Output 'Setup complete. Run .\run.ps1 -Task all'
