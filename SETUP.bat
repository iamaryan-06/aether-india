@echo off
setlocal enabledelayedexpansion
title AETHER INDIA - One-Time Setup
color 0B

echo =====================================================================
echo   AETHER INDIA -- 1-Click Automated Project Setup
echo =====================================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python (version 3.11 or newer) from:
    echo https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
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
    echo Please install Node.js (LTS version) from:
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
call venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
call venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo    Backend packages installed successfully!

:: Setup .env
if not exist ".env" (
    echo    Creating .env from .env.example...
    copy ".env.example" ".env" >nul
)

:: Seed Database & Embeddings
echo    Initializing SQLite database & ChromaDB vector store...
call venv\Scripts\python.exe seed.py
if %errorlevel% neq 0 (
    echo [WARNING] Seed script encountered a warning, continuing...
)

:: 4. Setup Frontend Dependencies
echo.
echo [4/5] Setting up Frontend dependencies (Next.js, Tailwind, etc.)...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo    Running npm install (this may take 1-2 minutes on first run)...
    call npm install
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to install npm packages.
        pause
        exit /b 1
    )
) else (
    echo    node_modules already present!
)

:: 5. Finished
cd /d "%~dp0"
color 0A
echo.
echo =====================================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo =====================================================================
echo.
echo All backend and frontend dependencies are ready.
echo You can now run the project at any time simply by double-clicking:
echo.
echo      START.bat
echo.
echo =====================================================================
pause
