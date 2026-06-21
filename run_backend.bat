@echo off
cd /d "%~dp0backend"
uvicorn main:app --host 0.0.0.0 --port 8117 --reload
pause
