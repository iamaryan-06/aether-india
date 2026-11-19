@echo off
setlocal enabledelayedexpansion
title AETHER INDIA - Launcher
color 0B

echo =====================================================================
echo   AETHER INDIA // 4-Agent LangGraph Operations Platform
echo =====================================================================
echo.

:: 1. Check prerequisites & auto-setup if not already done
if not exist "%~dp0backend\venv\Scripts\python.exe" (
    echo [NOTICE] First-time setup required. Launching automatic installer...
    echo.
    call "%~dp0SETUP.bat"
    if not exist "%~dp0backend\venv\Scripts\python.exe" (
        echo [ERROR] Setup did not complete. Exiting.
        pause
        exit /b 1
    )
)

if not exist "%~dp0backend\.env" (
    echo Creating backend\.env from template...
    copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
)

if not exist "%~dp0frontend\node_modules" (
    echo [NOTICE] Installing frontend dependencies first...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

:: 2. Terminate any previous dead instances on ports 8000 and 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

:: 3. Launch Backend in a separate window
echo [1/2] Starting FastAPI Backend on http://localhost:8000...
start "AETHER INDIA - Backend API [Port 8000]" cmd /k "title AETHER INDIA - Backend API [8000] && cd /d "%~dp0backend" && venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

:: 4. Launch Frontend in a separate window
echo [2/2] Starting Next.js Storefront on http://localhost:3000...
start "AETHER INDIA - Storefront [Port 3000]" cmd /k "title AETHER INDIA - Next.js UI [3000] && cd /d "%~dp0frontend" && npm run dev"

:: 5. Wait a few seconds for services to initialize
echo.
echo Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

:: 6. Auto-open default browser
start http://localhost:3000

color 0A
cls
echo =====================================================================
echo   AETHER INDIA IS RUNNING!
echo =====================================================================
echo.
echo   Customer Storefront : http://localhost:3000
echo   Admin Operations    : http://localhost:3000/admin
echo   FastAPI Swagger Docs: http://localhost:8000/docs
echo.
echo ---------------------------------------------------------------------
echo   DEMO CREDENTIALS:
echo   Customer: aarav@customer.com   / Demo@1234  (or 1-Click on /login)
echo   Admin   : admin@aether.in      / Demo@1234  (or 1-Click on /login)
echo ---------------------------------------------------------------------
echo.
echo   Two windows are running in the background:
echo     1) AETHER INDIA - Backend API [Port 8000]
echo     2) AETHER INDIA - Next.js UI  [Port 3000]
echo.
echo   To STOP everything cleanly, press any key below or run STOP.bat.
echo =====================================================================
echo.
pause

:: Cleanup when user presses any key
echo.
echo Stopping all AETHER INDIA servers...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo Done! Both servers stopped.
timeout /t 2 /nobreak >nul
exit /b 0
