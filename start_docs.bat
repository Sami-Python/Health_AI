@echo off
echo ===================================================
echo  Starting Health AI Docs Server (Robust Mode)
echo ===================================================

echo [1/3] Using Python from .venv...
REM Use the full path to the python executable in the virtual environment
REM This avoids issues with 'activate' not persisting or PATH issues

.\.venv\Scripts\python.exe -m mkdocs serve --clean

if errorlevel 1 (
    echo.
    echo ERROR: MkDocs failed to start.
    echo Please make sure you are in the 'health_ai' directory
    echo and that '.venv' exists.
    pause
    exit /b
)

pause
