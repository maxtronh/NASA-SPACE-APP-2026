@echo off
title Flame in Freefall — Full Docker Deployment
cd /d "%~dp0"
echo =====================================================================
echo    Launching Entire Stack via Docker Compose (DB + Backend + UI)...
echo =====================================================================
docker compose up --build
pause
