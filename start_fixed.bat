@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title AI Interview System - Start (Flask + Qwen-Omni + RAG)

echo ========================================
echo       AI Interview System - Start (Flask + Qwen-Omni + RAG)
echo ========================================
echo.

set PROJECT_ROOT=%~dp0

echo [INFO] Project root: %PROJECT_ROOT%
echo.

echo [1/2] Checking dependencies...
echo.

set DEP_MISSING=0

echo Checking Python...
python --version >nul 2>&1
if not errorlevel 1 goto python_ok
echo [ERROR] Python not found
echo Please install Python 3.10 or higher (required for dashscope)
echo Download: https://www.python.org/downloads/
set DEP_MISSING=1
goto python_done
:python_ok
echo [OK] Python found
:python_done

echo.
echo Checking Node.js...
node --version >nul 2>&1
if not errorlevel 1 goto node_ok
echo [ERROR] Node.js not found
echo Please install Node.js 18 or higher
echo Download: https://nodejs.org/
set DEP_MISSING=1
goto node_done
:node_ok
echo [OK] Node.js found
:node_done

echo.
if !DEP_MISSING! EQU 0 goto deps_ok

echo.
echo [ERROR] Missing required dependencies
echo Please install the missing software and try again
pause
exit /b 1

:deps_ok
echo [OK] All dependencies found
echo.

echo [2/2] Starting services...
echo.

echo [2.1] Starting Flask Backend Service (with Qwen-Omni integration)...
if not exist "%PROJECT_ROOT%backend\flask-backend\requirements.txt" (
    echo [ERROR] Flask backend not found at: %PROJECT_ROOT%backend\flask-backend\
    echo Please ensure Flask backend is properly set up
    pause
    exit /b 1
)
if exist "%PROJECT_ROOT%backend\flask-backend\venv\Scripts\activate.bat" (
    echo [INFO] Using Python virtual environment
    start "Flask Backend (Qwen-Omni)" cmd /k "cd /d "%PROJECT_ROOT%backend\flask-backend" && call venv\Scripts\activate.bat && python run.py"
) else (
    echo [WARNING] No virtual environment found, using system Python
    echo [NOTE] Virtual environment recommended for dependency isolation
    start "Flask Backend (Qwen-Omni)" cmd /k "cd /d "%PROJECT_ROOT%backend\flask-backend" && python run.py"
)
timeout /t 10 /nobreak >nul

echo [2.2] Starting Frontend Service (Vue.js with Qwen-Omni interface)...
if not exist "%PROJECT_ROOT%frontend\package.json" (
    echo [ERROR] Frontend not found at: %PROJECT_ROOT%frontend\
    echo Please ensure frontend is properly set up
    pause
    exit /b 1
)
start "Frontend Service (Qwen-Omni)" cmd /k "cd /d "%PROJECT_ROOT%frontend" && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo All services started!
echo.
echo URLs:
echo   Frontend: http://localhost:5173
echo   Flask Backend: http://localhost:8083
echo   Qwen-Omni WebSocket: ws://localhost:8083/qwen-omni-interview
echo   RAG Service: Enabled (local mode, chroma_db ready)
echo ========================================
echo.
echo [IMPORTANT] Before using Qwen-Omni interview:
echo 1. Ensure QWEN_OMNI_API_KEY is configured in backend\flask-backend\.env
echo 2. Choose "Qwen-Omni面试" option on the home page
echo 3. Traditional interview mode still available as backup
echo 4. RAG knowledge base provides contextual questions for better interviews
echo.
echo Opening frontend in browser...
start "" http://localhost:5173

echo.
echo Press any key to keep this window open...
pause >nul