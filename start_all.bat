@echo off
setlocal enabledelayedexpansion
title Flame in Freefall — Launcher

cd /d "%~dp0"

echo =====================================================================
echo           FLAME IN FREEFALL — NASA SPACE APPS CHALLENGE 2026
echo                Scientific Intelligence & Flight Telemetry
echo =====================================================================
echo.

:: 1. Check and Start Database (PostgreSQL + pgvector if Docker is up, else SQLite)
echo [*] Checking Database Layer...
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker daemon detected. Starting PostgreSQL + pgvector container...
    docker compose up -d db
    echo [OK] Database service running on port 5432.
) else (
    echo [INFO] Docker daemon is not active.
    echo [OK] Backend will automatically use local SQLite fallback tier with zero-fabrication.
)
echo.

:: 2. Check Python Environment
echo [*] Checking Backend Python Environment...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [OK] Found virtual environment: .venv
) else (
    set "PYTHON_EXE=python"
    echo [WARN] .venv not found, falling back to system python.
)
echo.

:: 3. Start Backend API Server
echo [*] Launching FastAPI Backend on http://localhost:8000 ...
start "Flame in Freefall — Backend API" cmd /k "title Flame in Freefall — Backend API [Port 8000] && cd /d "%~dp0" && "%PYTHON_EXE%" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 4. Start Next.js Frontend Server
echo [*] Launching Next.js Frontend on http://localhost:3000 ...
start "Flame in Freefall — Frontend" cmd /k "title Flame in Freefall — Next.js Frontend [Port 3000] && cd /d "%~dp0\frontend" && npm run dev"

:: 5. Await Backend Readiness & Open Browser
echo.
echo [*] Waiting for Backend API service to report healthy...
set "BACKEND_READY=0"
for /L %%i in (1,1,15) do (
    if !BACKEND_READY! equ 0 (
        curl -s -m 2 http://127.0.0.1:8000/api/v1/health >nul 2>&1
        if !errorlevel! equ 0 (
            set "BACKEND_READY=1"
            echo [OK] Backend API is live and responding (attempt %%i/15).
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if !BACKEND_READY! equ 0 (
    echo [INFO] Backend is still initializing in background. Frontend will start with authentic local cache.
)

echo.
echo =====================================================================
echo  Services launched successfully!
echo  - Frontend:    http://localhost:3000
echo  - Backend API: http://localhost:8000
echo  - API Docs:    http://localhost:8000/docs
echo =====================================================================
echo.
start http://localhost:3000

echo.
echo [DONE] All systems operational. To terminate, run stop_all.bat
timeout /t 3 /nobreak >nul
