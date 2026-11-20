@echo off
title AETHER INDIA - Backend (Port 8000)
color 0B
cd /d "%~dp0backend"
echo  Starting AETHER INDIA Backend on http://localhost:8000
echo  (Keep this window open while using the project)
echo.
venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
