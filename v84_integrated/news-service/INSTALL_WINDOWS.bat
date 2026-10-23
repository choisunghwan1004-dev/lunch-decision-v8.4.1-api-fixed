@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".env" (copy ".env.example" ".env" >nul & notepad ".env")
py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (echo pip install failed & pause & exit /b 1)
python -m pytest -q tests
if errorlevel 1 (echo tests failed & pause & exit /b 1)
python setup.py
if errorlevel 1 (echo database setup failed & pause & exit /b 1)
python live_check.py
if errorlevel 1 (echo database check failed & pause & exit /b 1)
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
