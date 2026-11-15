@echo off
title Flame in Freefall — Terminator
echo =====================================================================
echo             Stopping Flame in Freefall Services...
echo =====================================================================
echo.

:: Kill Python uvicorn processes on port 8000
echo [*] Stopping Backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Kill Node/Next.js processes on port 3000
echo [*] Stopping Frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Stop Docker DB container if running
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Stopping Docker DB container...
    docker stop flame_db >nul 2>&1
)

echo.
echo [OK] All Flame in Freefall services have been stopped.
timeout /t 3 /nobreak >nul
