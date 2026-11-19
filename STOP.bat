@echo off
title AETHER INDIA - Stop Servers
color 0C

echo =====================================================================
echo   AETHER INDIA -- Stopping All Running Servers
echo =====================================================================
echo.

echo Terminating backend process on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Killed process %%a on port 8000
)

echo Terminating frontend process on port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Killed process %%a on port 3000
)

color 0A
echo.
echo =====================================================================
echo   All AETHER INDIA services have been stopped successfully!
echo =====================================================================
timeout /t 2 /nobreak >nul
exit /b 0
