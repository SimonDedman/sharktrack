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
    echo Please install Python 3.12.10:
    echo   1. Download from: https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
    echo   2. IMPORTANT: Check "Add Python to PATH" during installation
    echo   3. Restart this script
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

REM Check Python version (3.13+ often has compatibility issues with ML libraries)
echo.
echo Checking Python version compatibility...
python -c "import sys; v=sys.version_info; exit(0 if v.major==3 and 10<=v.minor<=12 else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] Python version may not be compatible!
    echo           SharkTrack requires Python 3.10, 3.11, or 3.12
    echo           Python 3.13+ does NOT work with ML libraries like PyTorch
    echo.
    echo           Please install Python 3.12.10 from:
    echo           https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
    echo.
    timeout /t 5 >nul
)

REM Install/update dependencies
echo.
echo Installing dependencies (this may take a few minutes on first run)...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency installation failed!
    echo.
    echo Common causes:
    echo   1. Python version too new (3.13+) - install Python 3.12.10 from:
    echo      https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
    echo   2. No internet connection
    echo   3. Firewall blocking pip
    echo.
    echo Try running manually: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
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
