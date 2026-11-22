@echo off
cd /d "%~dp0frontend"
echo ========================================================
echo  Starting ReleaseShield Frontend Dashboard (Vite + React)
echo  URL: http://localhost:5173
echo ========================================================
pnpm run dev
pause

