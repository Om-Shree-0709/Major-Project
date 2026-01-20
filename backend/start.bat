@echo off
echo ============================================================
echo  STARTING MCP FRAMEWORK BACKEND
echo ============================================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start server
python server.py
