@echo off
setlocal enabledelayedexpansion
title AETHER INDIA - One-Time Setup
color 0B

echo =====================================================================
echo   AETHER INDIA -- 1-Click Automated Project Setup
echo   4-Agent LangGraph E-Commerce Platform
echo =====================================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not in your system PATH!
    echo.
    echo Please install Python 3.11 or newer from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo    Found: %%v

:: 2. Check Node.js & npm
echo.
echo [2/5] Checking Node.js and npm...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Node.js is not installed or not in your system PATH!
    echo.
    echo Please install Node.js LTS from:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do echo    Found Node.js: %%v
for /f "tokens=*" %%v in ('npm --version') do echo    Found npm: %%v

:: 3. Setup Backend Virtual Environment & Dependencies
echo.
echo [3/5] Setting up Backend Python Virtual Environment...
cd /d "%~dp0backend"
if not exist "venv\Scripts\python.exe" (
    echo    Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo    Installing backend requirements (FastAPI, LangGraph, ChromaDB, etc.)...
echo    This may take 3-5 minutes on first run...
call venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
call venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo    Backend packages installed successfully!

:: 4. Configure API Key (.env)
echo.
echo [4/5] Configuring API Keys...
if not exist ".env" (
    echo    Creating .env from .env.example...
    copy ".env.example" ".env" >nul

    echo.
    echo =====================================================================
    echo   ACTION REQUIRED: Enter Your Gemini API Key
    echo =====================================================================
    echo.
    echo   This project uses Google Gemini AI (FREE tier available).
    echo   Get your free API key at: https://aistudio.google.com/apikey
    echo.
    echo   You can also use Groq (FREE): https://console.groq.com/keys
    echo   Or OpenAI: https://platform.openai.com/api-keys
    echo.
    set /p USER_API_KEY="   Paste your GOOGLE_API_KEY here (press Enter to skip): "

    if not "!USER_API_KEY!"=="" (
        :: Replace placeholder in .env using PowerShell
        powershell -Command "(Get-Content '.env') -replace 'GOOGLE_API_KEY=AIza\.\.\.', 'GOOGLE_API_KEY=!USER_API_KEY!' | Set-Content '.env'"
        echo    API Key saved to .env successfully!
    ) else (
        echo    [SKIPPED] You can edit backend\.env manually before running the project.
    )
) else (
    echo    .env already exists, skipping...
)

:: Seed Database & Embeddings
echo    Initializing SQLite database and ChromaDB vector store...
echo    (Building local AI embeddings - may take 1-2 minutes on first run)
call venv\Scripts\python.exe seed.py
if %errorlevel% neq 0 (
    echo [WARNING] Seed script returned a warning - this may be normal if DB already seeded.
)

:: 5. Setup Frontend Dependencies
echo.
echo [5/5] Setting up Frontend (Next.js, Tailwind CSS, React)...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo    Running npm install (this may take 1-2 minutes)...
    call npm install
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to install npm packages.
        pause
        exit /b 1
    )
) else (
    echo    node_modules already present, skipping...
)

:: Done!
cd /d "%~dp0"
color 0A
echo.
echo =====================================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo =====================================================================
echo.
echo   All backend and frontend dependencies are ready.
echo.
echo   Next Step: Double-click START.bat to launch the project!
echo.
echo   REMINDER: If you skipped entering an API key above,
echo   edit backend\.env and add your GOOGLE_API_KEY before starting.
echo.
echo =====================================================================
pause
