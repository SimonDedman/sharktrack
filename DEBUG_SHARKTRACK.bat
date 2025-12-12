@echo off
echo Step 1: Script started
pause

cd /d "%~dp0"
echo Step 2: Changed to script directory: %cd%
pause

echo Step 3: Checking Python...
python --version
echo Python check done (errorlevel: %errorlevel%)
pause

echo Step 4: Checking if venv exists...
if exist "sharktrack-env" (
    echo    venv EXISTS
) else (
    echo    venv does NOT exist
)
pause

echo Step 5: Activating venv...
call sharktrack-env\Scripts\activate.bat
echo Activation done (errorlevel: %errorlevel%)
pause

echo Step 6: Checking Python in venv...
where python
python --version
pause

echo Step 7: Testing Flask import...
python -c "import flask; print('Flask OK:', flask.__version__)"
echo Flask test done (errorlevel: %errorlevel%)
pause

echo Step 8: About to start server...
echo If window closes after this, the Python script is crashing
pause

python start_sharktrack.py

echo Step 9: Server exited (errorlevel: %errorlevel%)
pause
