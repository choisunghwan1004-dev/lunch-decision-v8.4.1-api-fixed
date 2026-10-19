@echo off
cd /d "%~dp0.."
python -m pip install -r news_service\requirements.txt
if errorlevel 1 (pause & exit /b 1)
python -m uvicorn news_service.app:app --host 127.0.0.1 --port 8001
pause
