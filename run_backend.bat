@echo off
set "PYTHON_EXE=C:\Users\shree\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
cd /d "%~dp0backend"
set "PYTHONPATH=%cd%\.venv\Lib\site-packages;%cd%"
echo ========================================================
echo  Starting ReleaseShield Backend Server (FastAPI + XGBoost)
echo  URL: http://localhost:8000  ^|  Docs: http://localhost:8000/docs
echo ========================================================
"%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause

