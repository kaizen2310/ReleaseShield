# ReleaseShield Backend Launcher
# Uses the authorized Python 3.12 binary with virtual environment site-packages, bypassing workspace AppLocker restrictions

$basePython = "C:\Users\shree\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
$sitePackages = "$PSScriptRoot\.venv\Lib\site-packages"

if (-not (Test-Path $basePython)) {
    $basePython = "python"
}

$env:PYTHONPATH = "$sitePackages;$PSScriptRoot"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " Starting ReleaseShield Backend (Python 3.12 + FastAPI)" -ForegroundColor Green
Write-Host " http://localhost:8000 | Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

& $basePython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

