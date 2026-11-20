@echo off
title AETHER INDIA - Launcher
color 0B

:: ══════════════════════════════════════════════════
::  First-time setup check
:: ══════════════════════════════════════════════════
if not exist "%~dp0backend\venv\Scripts\python.exe" (
    echo  [NOTICE] Running first-time setup...
    call "%~dp0SETUP.bat"
    if not exist "%~dp0backend\venv\Scripts\python.exe" (
        echo  [ERROR] Setup failed. Exiting.
        pause & exit /b 1
    )
)

if not exist "%~dp0frontend\node_modules" (
    echo  [NOTICE] Running first-time setup...
    call "%~dp0SETUP.bat"
)

:: ══════════════════════════════════════════════════
::  Kill any old processes on 8000 / 3000
:: ══════════════════════════════════════════════════
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1

:: ══════════════════════════════════════════════════
::  Launch both servers in separate windows
:: ══════════════════════════════════════════════════
echo.
echo  [1/2] Starting Backend...
start "" "%~dp0_run_backend.bat"

echo  [2/2] Starting Frontend...
start "" "%~dp0_run_frontend.bat"

:: ══════════════════════════════════════════════════
::  Wait and open browser
:: ══════════════════════════════════════════════════
echo.
echo  Waiting for servers to start (12 seconds)...
timeout /t 12 /nobreak >nul
start http://localhost:3000

color 0A
cls
echo.
echo  ================================================================
echo    AETHER INDIA IS RUNNING!
echo  ================================================================
echo.
echo    Customer Storefront : http://localhost:3000
echo    Admin Dashboard     : http://localhost:3000/admin
echo    API Docs            : http://localhost:8000/docs
echo.
echo  ----------------------------------------------------------------
echo    DEMO LOGIN:
echo    Customer : aarav@customer.com  /  Demo@1234
echo    Admin    : admin@aether.in     /  Demo@1234
echo    (Or use the 1-Click Demo button on the login page)
echo  ----------------------------------------------------------------
echo.
echo    Two windows are running in the background.
echo    Press any key here to STOP everything.
echo  ================================================================
echo.
pause >nul

:: ══════════════════════════════════════════════════
::  Stop on keypress
:: ══════════════════════════════════════════════════
color 0C
echo  Stopping servers...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
echo  Done! All servers stopped.
timeout /t 2 /nobreak >nul
