#!/usr/bin/env pwsh
# ReleaseShield — Test Suite Runner (PowerShell)
# Usage:
#   .\run_tests.ps1          # full suite (includes slow AI-pipeline tests)
#   .\run_tests.ps1 fast     # fast suite only (skips AI-pipeline tests, ~3s)
#   .\run_tests.ps1 coverage # fast suite + coverage report

param(
    [string]$Mode = "full"
)

$PythonExe = "C:\Users\shree\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
$BackendDir = $PSScriptRoot
$env:PYTHONPATH = "$BackendDir\.venv\Lib\site-packages;$BackendDir"

Set-Location $BackendDir

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ReleaseShield — Test Suite Runner" -ForegroundColor Cyan
Write-Host "  Python  : $PythonExe" -ForegroundColor Gray
Write-Host "  Backend : $BackendDir" -ForegroundColor Gray
Write-Host "  Mode    : $Mode" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$SkipArgs = @()
$CoverageArgs = @()

switch ($Mode.ToLower()) {
    "fast" {
        Write-Host "[MODE] Fast — skipping live AI-pipeline tests" -ForegroundColor Yellow
        $SkipArgs = @(
            "--ignore=tests\test_integration_extended.py",
            "--ignore=tests\test_orchestrator_nodes.py"
        )
    }
    "coverage" {
        Write-Host "[MODE] Coverage — fast tests + HTML coverage report" -ForegroundColor Yellow
        $SkipArgs = @(
            "--ignore=tests\test_integration_extended.py",
            "--ignore=tests\test_orchestrator_nodes.py"
        )
        $CoverageArgs = @("--cov=app", "--cov-report=html:htmlcov", "--cov-report=term-missing")
    }
    default {
        Write-Host "[MODE] Full — all tests including AI-pipeline (may take several minutes)" -ForegroundColor Yellow
        Write-Host "        Tip: run with 'fast' argument to skip AI tests: .\run_tests.ps1 fast" -ForegroundColor DarkGray
    }
}

Write-Host ""

# Run pytest
& $PythonExe -m pytest tests\ -v --tb=short @SkipArgs @CoverageArgs
$ExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if ($ExitCode -eq 0) {
    Write-Host "  ✅ ALL TESTS PASSED  (exit 0)" -ForegroundColor Green
} else {
    Write-Host "  ❌ SOME TESTS FAILED  (exit $ExitCode)" -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

exit $ExitCode
