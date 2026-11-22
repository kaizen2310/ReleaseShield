@echo off
setlocal enabledelayedexpansion

set "PYTHON_EXE=C:\Users\shree\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
cd /d "%~dp0backend"
set "PYTHONPATH=%cd%\.venv\Lib\site-packages;%cd%"

echo.
echo ============================================================
echo   ReleaseShield — Test Suite Runner
echo   Python: %PYTHON_EXE%
echo   Scope : backend\tests\  (all test files)
echo ============================================================
echo.

REM Parse optional argument: "fast" skips the slow AI-integration tests
set "SKIP_AI="
if /i "%~1"=="fast" (
    set "SKIP_AI=--ignore=tests\test_integration_extended.py --ignore=tests\test_orchestrator_nodes.py"
    echo [MODE] Fast mode: skipping live AI-pipeline tests
    echo.
) else (
    echo [MODE] Full mode: including live AI-pipeline tests (may take several minutes)
    echo         Run with argument "fast" to skip AI tests: run_tests.bat fast
    echo.
)

REM Run pytest
"%PYTHON_EXE%" -m pytest tests\ -v --tb=short %SKIP_AI%

echo.
echo ============================================================
echo   Done. Exit code: %ERRORLEVEL%
echo ============================================================
echo.
pause
endlocal
