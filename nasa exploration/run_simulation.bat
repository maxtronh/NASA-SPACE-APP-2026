@echo off
REM NASA Solar System 25-Faces Simulation Launcher
REM Milestone M9 Showcase

echo =======================================================
echo Starting NASA Solar System 25-Faces Simulation...
echo =======================================================

cd /d "%~dp0"
python run_simulation.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] Simulation server terminated with an error code.
    pause
)
