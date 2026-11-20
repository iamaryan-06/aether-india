@echo off
title AETHER INDIA - Frontend (Port 3000)
color 0B
cd /d "%~dp0frontend"
echo  Starting AETHER INDIA Frontend on http://localhost:3000
echo  (Keep this window open while using the project)
echo.

:: Try npm from PATH first (most users have this)
where npm >nul 2>&1
if %errorlevel%==0 (
    npm run dev
    goto :end
)

:: Fallback: use node.exe directly with known next.js path
set "NODEEXE="
if exist "C:\Program Files\nodejs\node.exe"            set "NODEEXE=C:\Program Files\nodejs\node.exe"
if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe"     set "NODEEXE=%LOCALAPPDATA%\Programs\nodejs\node.exe"
if exist "%ProgramFiles(x86)%\nodejs\node.exe"         set "NODEEXE=%ProgramFiles(x86)%\nodejs\node.exe"

:: Also read path saved by SETUP.bat
if "%NODEEXE%"=="" if exist "%~dp0.node_path" set /p NODEEXE=<"%~dp0.node_path"

if not "%NODEEXE%"=="" (
    "%NODEEXE%" ".\node_modules\next\dist\bin\next" dev -p 3000
    goto :end
)

color 0C
echo [ERROR] Node.js not found!
echo Please run SETUP.bat first, or install Node.js from https://nodejs.org/

:end
pause
