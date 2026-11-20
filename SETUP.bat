@echo off
setlocal enabledelayedexpansion
title AETHER INDIA - First Time Setup
color 0B

echo.
echo  ================================================================
echo    AETHER INDIA - First Time Setup
echo    This runs ONCE. After this, just double-click START.bat
echo  ================================================================
echo.

:: ══════════════════════════════════════════════════
::  STEP 1 — Find Python
:: ══════════════════════════════════════════════════
echo [1/5] Looking for Python...

set PYTHON=
:: Try PATH first (works if user installed Python with "Add to PATH")
python --version >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('where python') do if "!PYTHON!"=="" set PYTHON=%%i
)
:: Fallback: common install locations
if not exist "!PYTHON!" set PYTHON=
if "!PYTHON!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
if "!PYTHON!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if "!PYTHON!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if "!PYTHON!"=="" if exist "C:\Program Files\Python313\python.exe"               set PYTHON=C:\Program Files\Python313\python.exe
if "!PYTHON!"=="" if exist "C:\Program Files\Python312\python.exe"               set PYTHON=C:\Program Files\Python312\python.exe
if "!PYTHON!"=="" if exist "C:\Program Files\Python311\python.exe"               set PYTHON=C:\Program Files\Python311\python.exe
if "!PYTHON!"=="" if exist "C:\Python313\python.exe"                             set PYTHON=C:\Python313\python.exe
if "!PYTHON!"=="" if exist "C:\Python312\python.exe"                             set PYTHON=C:\Python312\python.exe
if "!PYTHON!"=="" if exist "C:\Python311\python.exe"                             set PYTHON=C:\Python311\python.exe

if "!PYTHON!"=="" (
    color 0C
    echo.
    echo  [ERROR] Python 3.11+ not found on this computer!
    echo.
    echo  Please install Python from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)
echo         Found: !PYTHON!

:: ══════════════════════════════════════════════════
::  STEP 2 — Find Node.js / npm
:: ══════════════════════════════════════════════════
echo.
echo [2/5] Looking for Node.js...

set NODE=
set NPM=
:: Try PATH first
node --version >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('where node') do if "!NODE!"=="" set NODE=%%i
    for /f "tokens=*" %%i in ('where npm')  do if "!NPM!"==""  set NPM=%%i
)
:: Fallback: common install locations
if "!NODE!"=="" if exist "C:\Program Files\nodejs\node.exe" (
    set NODE=C:\Program Files\nodejs\node.exe
    set NPM=C:\Program Files\nodejs\npm.cmd
)
if "!NODE!"=="" if exist "%ProgramFiles(x86)%\nodejs\node.exe" (
    set NODE=%ProgramFiles(x86)%\nodejs\node.exe
    set NPM=%ProgramFiles(x86)%\nodejs\npm.cmd
)

if "!NODE!"=="" (
    color 0C
    echo.
    echo  [ERROR] Node.js not found on this computer!
    echo.
    echo  Please install Node.js LTS from: https://nodejs.org/
    echo  (Use all default options during installation)
    echo.
    pause
    exit /b 1
)
echo         Found Node: !NODE!

:: Save paths for START.bat to use
echo !PYTHON!> "%~dp0.python_path"
echo !NODE!>   "%~dp0.node_path"

:: ══════════════════════════════════════════════════
::  STEP 3 — Create Python Virtual Environment
:: ══════════════════════════════════════════════════
echo.
echo [3/5] Setting up Python backend...
cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo         Creating virtual environment...
    "!PYTHON!" -m venv venv
    if %errorlevel% neq 0 (
        color 0C & echo [ERROR] Failed to create virtual environment. & pause & exit /b 1
    )
)

echo         Installing Python packages (3-5 min on first run)...
call venv\Scripts\python.exe -m pip install --upgrade pip -q
call venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C & echo [ERROR] Failed to install Python packages. & pause & exit /b 1
)
echo         Python packages installed!

:: ══════════════════════════════════════════════════
::  STEP 4 — API Key Setup
:: ══════════════════════════════════════════════════
echo.
echo [4/5] Configuring API Key...

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo  ================================================================
    echo   ACTION REQUIRED: Paste your FREE Google Gemini API Key
    echo  ================================================================
    echo.
    echo   Get your free key (takes 30 seconds):
    echo   1. Go to: https://aistudio.google.com/apikey
    echo   2. Click "Create API Key"
    echo   3. Copy the key and paste it below
    echo.
    set /p APIKEY="  Paste your GOOGLE_API_KEY here (or press Enter to skip): "
    if not "!APIKEY!"=="" (
        powershell -Command "(Get-Content '.env') -replace 'GOOGLE_API_KEY=AIza\.\.\.', 'GOOGLE_API_KEY=!APIKEY!' | Set-Content '.env'"
        echo         API key saved!
    ) else (
        echo         Skipped. Edit backend\.env later to add your key.
    )
) else (
    echo         .env already configured.
)

:: Seed the database
echo         Setting up database...
call venv\Scripts\python.exe seed.py
echo         Database ready!

:: ══════════════════════════════════════════════════
::  STEP 5 — Install Frontend packages
:: ══════════════════════════════════════════════════
echo.
echo [5/5] Installing frontend packages...
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo         Running npm install (1-2 min)...
    if exist "!NPM!" (
        call "!NPM!" install
    ) else (
        call "!NODE!" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install
    )
    if %errorlevel% neq 0 (
        color 0C & echo [ERROR] npm install failed. & pause & exit /b 1
    )
) else (
    echo         node_modules already installed.
)

cd /d "%~dp0"

:: ══════════════════════════════════════════════════
::  DONE
:: ══════════════════════════════════════════════════
color 0A
echo.
echo  ================================================================
echo    SETUP COMPLETE!
echo    Now double-click START.bat to launch the project!
echo  ================================================================
echo.
pause
