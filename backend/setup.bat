@echo off
echo ============================================================
echo  UNIFIED MCP FRAMEWORK - BACKEND SETUP
echo ============================================================
echo.

echo [1/4] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Creating new virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

echo [2/4] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [3/4] Installing dependencies...
pip install -r requirements.txt --quiet

echo [4/4] Setup complete!
echo.
echo ============================================================
echo  READY TO START
echo ============================================================
echo.
echo Run: python start_server.py
echo.
pause
