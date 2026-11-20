@echo off
title AETHER INDIA - Stop Servers
color 0C

echo =====================================================================
echo   AETHER INDIA -- Stopping All Running Servers
echo =====================================================================
echo.

echo Terminating backend process on port 8000...
set KILLED_BACKEND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo    Stopped PID %%a (Backend)
    set KILLED_BACKEND=1
)
if %KILLED_BACKEND%==0 echo    No process found on port 8000.

echo.
echo Terminating frontend process on port 3000...
set KILLED_FRONTEND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo    Stopped PID %%a (Frontend)
    set KILLED_FRONTEND=1
)
if %KILLED_FRONTEND%==0 echo    No process found on port 3000.

color 0A
echo.
echo =====================================================================
echo   All AETHER INDIA services stopped successfully!
echo =====================================================================
timeout /t 2 /nobreak >nul
exit /b 0
