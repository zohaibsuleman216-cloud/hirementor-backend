@echo off
cd /d "%~dp0"
set PYTHONPATH=%cd%
echo Starting SPB Backend Server...
echo API Docs will be at: http://127.0.0.1:8000/docs
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
