@echo off
REM ==========================================
REM SharkTrack Launcher for Windows
REM Double-click this file to start SharkTrack
REM ==========================================

title SharkTrack - Marine Video Analysis
cd /d "%~dp0"

echo.
echo ==========================================
echo       SharkTrack - Marine Video Analysis
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10 or later:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download Python 3.10 or later
    echo   3. IMPORTANT: Check "Add Python to PATH" during installation
    echo   4. Restart this script
    echo.
    pause
    exit /b 1
)

echo [OK] Python found

REM Check for GPU support
echo.
echo Checking GPU availability...
python -c "import torch; print('[OK] CUDA Available:', torch.cuda.is_available()); print('    GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')" 2>nul
if errorlevel 1 (
    echo [INFO] PyTorch not yet installed - will be installed shortly
)

REM Create virtual environment if it doesn't exist
if not exist "sharktrack-env" (
    echo.
    echo Creating virtual environment...
    python -m venv sharktrack-env
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call sharktrack-env\Scripts\activate.bat

REM Install/update dependencies
echo.
echo Checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed to install
    echo           SharkTrack may still work, continuing...
)

REM Install Flask if needed
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing Flask...
    pip install -q flask
)

REM Create required directories
if not exist "models" mkdir models
if not exist "templates" mkdir templates
if not exist "static" mkdir static

REM Check if config exists, create default if not
if not exist "sharktrack_config.json" (
    echo.
    echo [INFO] Creating default configuration file...
    python utils\config_loader.py --create
)

echo.
echo ==========================================
echo Starting SharkTrack Web Interface...
echo ==========================================
echo.
echo Your browser will open automatically.
echo If not, navigate to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the web GUI
python start_sharktrack.py

REM If the above fails, try the old method
if errorlevel 1 (
    echo.
    echo [INFO] Trying alternative launch method...
    python web_gui.py
)

pause
