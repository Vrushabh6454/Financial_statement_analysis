@echo off
setlocal enabledelayedexpansion

REM ===================================================================
REM Financial Statement Analysis System - Automatic Setup and Run Script
REM ===================================================================

echo ===============================================
echo Financial Statement Analysis System
echo Setting up environment and starting services...
echo ===============================================

REM Stop any existing services
call :STOP_SERVICES_SILENT

REM Set up the environment and start services
call :SETUP
if %errorlevel% neq 0 (
    echo ERROR: Setup failed. Exiting...
    pause
    exit /b 1
)

call :START_SERVICES
if %errorlevel% neq 0 (
    echo ERROR: Failed to start services. Exiting...
    pause
    exit /b 1
)

goto :EOF

:MENU
REM This function is kept for compatibility but not used in automatic mode
call :SETUP
if %errorlevel% neq 0 exit /b 1
call :START_SERVICES
if %errorlevel% neq 0 exit /b 1
exit /b 0

:SETUP
echo ===============================================
echo Setting up environment
echo ===============================================

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    exit /b 1
)

REM Check if Node.js is installed
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js.
    exit /b 1
)

REM Delete existing venv if it exists to ensure clean environment
if exist venv (
    echo Removing existing virtual environment...
    rd /s /q venv
)

REM Create fresh virtual environment
echo Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    exit /b 1
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies in virtual environment...
pip install -r npnonlyf\requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies.
    call venv\Scripts\deactivate.bat
    exit /b 1
)

echo Creating data directories...
if not exist data\pdfs mkdir data\pdfs
if not exist data\output mkdir data\output
if not exist data\embeddings mkdir data\embeddings

echo Installing Node dependencies...
cd client
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node.js dependencies.
    cd ..
    call venv\Scripts\deactivate.bat
    exit /b 1
)
cd ..

call venv\Scripts\deactivate.bat

echo ===============================================
echo Environment setup completed successfully!
echo ===============================================
exit /b 0

:START_SERVICES
echo ===============================================
echo Starting services
echo ===============================================

REM Kill existing processes if any
call :STOP_SERVICES_SILENT

REM Activate the virtual environment
call venv\Scripts\activate.bat

echo Starting Flask backend server...
start cmd /k "title Financial Analysis Backend && color 0A && call venv\Scripts\activate.bat && python server.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting React frontend...
cd client
start cmd /k "title Financial Analysis Frontend && color 0B && npm run dev"
cd ..

call venv\Scripts\deactivate.bat

echo ===================================
echo All services started successfully!
echo ===================================
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo ===================================
echo Note: To stop services, select option 3 or run "run_app.bat stop"
echo ===============================================
exit /b 0

:STOP_SERVICES
echo ===============================================
echo Stopping services
echo ===============================================
call :STOP_SERVICES_SILENT
echo All services stopped successfully!
exit /b 0

:STOP_SERVICES_SILENT
REM Kill any running Node.js processes (frontend)
tasklist /FI "IMAGENAME eq node.exe" /NH | find "node.exe" > nul
if %errorlevel% equ 0 (
    taskkill /F /IM node.exe > nul 2>&1
)

REM Kill any running Python processes (backend)
tasklist /FI "IMAGENAME eq python.exe" /NH | find "python.exe" > nul
if %errorlevel% equ 0 (
    taskkill /F /IM python.exe > nul 2>&1
)

REM Close any command windows we opened
tasklist /FI "WINDOWTITLE eq Financial Analysis Backend" /NH > nul 2>&1
if %errorlevel% equ 0 (
    taskkill /F /FI "WINDOWTITLE eq Financial Analysis Backend" > nul 2>&1
)

tasklist /FI "WINDOWTITLE eq Financial Analysis Frontend" /NH > nul 2>&1
if %errorlevel% equ 0 (
    taskkill /F /FI "WINDOWTITLE eq Financial Analysis Frontend" > nul 2>&1
)
exit /b 0

:CLEANUP
echo ===============================================
echo Cleaning up environment
echo ===============================================

REM Stop all services first
call :STOP_SERVICES_SILENT

REM Delete virtual environment without asking
echo Removing virtual environment...
if exist venv rd /s /q venv

REM Delete data folders without asking
echo Removing data folders...
if exist data rd /s /q data

echo ===============================================
echo Cleanup completed successfully!
echo ===============================================
exit /b 0

:HELP
echo ===============================================
echo Financial Statement Analysis System - Help
echo ===============================================
echo.
echo Usage: run_app.bat [ACTION]
echo.
echo Actions:
echo   setup   - Set up Python virtual environment and install dependencies
echo   start   - Start backend and frontend services
echo   stop    - Stop all running services
echo   clean   - Clean up environment (remove venv and data folders)
echo.
echo If no action is specified, an interactive menu will be displayed.
echo ===============================================
exit /b 0
