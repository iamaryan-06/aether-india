@echo off
title AETHER INDIA - Stopping...
color 0C

echo.
echo  ================================================================
echo    AETHER INDIA - Stopping All Servers
echo  ================================================================
echo.

set STOPPED=0

echo  Stopping Backend (port 8000)...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    echo         Stopped PID %%p
    set STOPPED=1
)
if %STOPPED%==0 echo         (not running)

set STOPPED=0
echo  Stopping Frontend (port 3000)...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    echo         Stopped PID %%p
    set STOPPED=1
)
if %STOPPED%==0 echo         (not running)

color 0A
echo.
echo  All done! Servers stopped.
echo.
timeout /t 2 /nobreak >nul
