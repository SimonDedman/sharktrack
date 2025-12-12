@echo off
REM ==========================================
REM SharkTrack Launcher for Windows
REM Double-click this file to start SharkTrack
REM ==========================================

title SharkTrack - Marine Video Analysis
cd /d "%~dp0"

REM Ensure we always pause at the end, even on errors
goto :main

:end
echo.
echo ==========================================
echo Press any key to close this window...
echo ==========================================
pause
exit /b

:main

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
    goto :end
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
        goto :end
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
echo Installing dependencies (this may take 5-10 minutes on first run)...
echo.
echo NOTE: PyTorch and Ultralytics are large packages (several GB).
echo       The install may appear to pause - this is normal, please wait.
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
    goto :end
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

REM Test network access (triggers Windows Firewall prompt if needed)
echo.
echo Checking network access...
echo (If Windows Firewall asks, click ALLOW)
echo.
python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 5000)); s.close(); print('[OK] Network access confirmed')"
if errorlevel 1 (
    echo.
    echo [WARNING] Could not bind to port 5000
    echo          Port may be in use, or firewall is blocking Python
    echo.
)

echo.
echo ==========================================
echo Starting SharkTrack server...
echo ==========================================
echo.
echo Once the server starts, open this URL in your browser:
echo.
echo    http://localhost:5000
echo.
echo (Keep this window open - it runs the server)
echo (Press Ctrl+C to stop)
echo ==========================================
echo.

REM Start the web GUI
python start_sharktrack.py

if errorlevel 1 (
    echo [ERROR] SharkTrack failed to start.
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo   - Missing dependencies: run "pip install -r requirements.txt"
    echo   - Port 5000 in use: close other applications using that port
    echo.
)

goto :end
