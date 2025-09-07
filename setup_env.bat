@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo Setting up Python environment for Financial Statement Analysis
echo ===============================================

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install setuptools and wheel first
echo Installing setuptools and wheel...
python -m pip install setuptools wheel

REM Install requests and its dependencies
echo Installing requests and its dependencies...
python -m pip install requests idna chardet charset-normalizer

REM Install all requirements
echo Installing requirements...
python -m pip install -r requirements.txt

echo ===============================================
echo Environment setup complete!
echo ===============================================
echo.
echo You can now run the application with:
echo run_app.bat
echo.
echo Or run the tests with:
echo python test_fixes.py
echo ===============================================

endlocal
