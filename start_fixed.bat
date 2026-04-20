@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title AI Video Interview System - Start (Qwen-Omni Realtime Video + RAG)

echo ========================================
echo       AI Video Interview System - Start
echo ========================================
echo   Core Features: Qwen-Omni Realtime Video + RAG Enhancement
echo ========================================
echo.

set PROJECT_ROOT=%~dp0

echo [INFO] Project root: %PROJECT_ROOT%
echo.

echo [1/3] Checking dependencies...
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
echo Please install Node.js ^>=20.19.0 or ^>=22.12.0 (as specified in package.json)
echo Download: https://nodejs.org/
echo Recommended: Download LTS version (Long Term Support)
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

echo [2/3] Checking configuration and environment...
echo.

:: Check MySQL connectivity
echo Checking MySQL connectivity...
where mysql >nul 2>&1
if errorlevel 1 (
    echo [WARNING] MySQL client not found in PATH
    echo Database functionality may be limited
    echo Install MySQL if needed for full functionality
) else (
    echo Testing MySQL connection with default credentials...
    mysql --host=localhost --port=3306 --user=root --password=123456 --execute="SELECT 1;" > nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Cannot connect to MySQL with default credentials (root/123456)
        echo Please update database credentials in backend\flask-backend\.env if different
        echo.
    ) else (
        echo [OK] MySQL connection successful
        :: Check if database exists
        mysql --host=localhost --port=3306 --user=root --password=123456 --execute="SHOW DATABASES LIKE 'ai_interview';" | findstr "ai_interview" > nul
        if errorlevel 1 (
            echo [INFO] Database 'ai_interview' does not exist yet
            echo It will be created when Flask backend starts
        ) else (
            echo [OK] Database 'ai_interview' exists
        )
    )
)

:: Check .env file
echo Checking Flask backend configuration...
cd /d "%PROJECT_ROOT%backend\flask-backend"
if not exist ".env" (
    echo [ERROR] .env file not found in backend\flask-backend\
    echo Please create .env file from .env.example or run install.bat
    echo.
    choice /c yn /m "Continue without .env file? (application may fail) (y/n): "
    if errorlevel 2 (
        echo Start cancelled
        pause
        exit /b 1
    )
    echo [WARNING] Starting without .env file - application may fail
) else (
    echo [OK] .env file found
    :: Check if API key is configured (warning only)
    findstr /i "VIDEO_CHAT_API_KEY" .env | findstr /v "^#" | findstr "your-qwen-omni-api-key-here" > nul
    if not errorlevel 1 (
        echo [WARNING] VIDEO_CHAT_API_KEY appears to be using default value
        echo Video interview will not work without a valid Qwen-Omni API key
    )
)

:: Check port availability
echo Checking port availability...
netstat -an | findstr ":8083" > nul
if not errorlevel 1 (
    echo [WARNING] Port 8083 is in use (Flask backend)
    echo You may need to change port in backend\flask-backend\run.py
)
netstat -an | findstr ":5173" > nul
if not errorlevel 1 (
    echo [WARNING] Port 5173 is in use (Frontend dev server)
    echo You may need to change port in frontend\vite.config.ts
)

echo.
echo [OK] Configuration check completed
echo.

echo [3/3] Starting services...
echo.

echo [2.1] Starting Flask Backend Service (Video Interview + RAG)...
if not exist "%PROJECT_ROOT%backend\flask-backend\requirements.txt" (
    echo [ERROR] Flask backend not found at: %PROJECT_ROOT%backend\flask-backend\
    echo Please ensure Flask backend is properly set up
    pause
    exit /b 1
)
if exist "%PROJECT_ROOT%backend\flask-backend\venv\Scripts\activate.bat" (
    echo [INFO] Using Python virtual environment
    start "Flask Backend (Video Interview + RAG)" cmd /k "cd /d "%PROJECT_ROOT%backend\flask-backend" && call venv\Scripts\activate.bat && python run.py"
) else (
    echo [WARNING] No virtual environment found, using system Python
    echo [NOTE] Virtual environment recommended for dependency isolation
    start "Flask Backend (Video Interview + RAG)" cmd /k "cd /d "%PROJECT_ROOT%backend\flask-backend" && python run.py"
)
timeout /t 10 /nobreak >nul

echo Verifying Flask backend startup...
set VERIFY_ATTEMPTS=0
:verify_backend
set /a VERIFY_ATTEMPTS+=1
echo Attempt !VERIFY_ATTEMPTS!/5: Checking backend health...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8083/api/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Flask backend is running and healthy
    goto backend_verified
)
if !VERIFY_ATTEMPTS! GEQ 5 (
    echo [WARNING] Flask backend may not have started properly
    echo Continuing anyway, but the backend may not be available
    goto backend_failed
)
timeout /t 3 /nobreak >nul
goto verify_backend
:backend_verified
:backend_failed

echo [2.2] Starting Frontend Service (Video Interview Interface)...
if not exist "%PROJECT_ROOT%frontend\package.json" (
    echo [ERROR] Frontend not found at: %PROJECT_ROOT%frontend\
    echo Please ensure frontend is properly set up
    pause
    exit /b 1
)
start "Frontend Service (Video Interview)" cmd /k "cd /d "%PROJECT_ROOT%frontend" && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo All services started! Video Interview System Ready
echo ========================================
echo.
echo URLs:
echo   Frontend (Video Interview): http://localhost:5173
echo   Flask Backend (API + WebSocket): http://localhost:8083
echo   Video WebSocket: ws://localhost:8083/video_chat
echo   RAG Service: Enabled (local mode, chroma_db ready)
echo ========================================
echo.
echo [IMPORTANT] Before starting video interview:
echo 1. Ensure VIDEO_CHAT_API_KEY is configured in backend\flask-backend\.env
echo 2. Select a position on the home page and start video interview
echo 3. Grant camera and microphone permissions when prompted
echo 4. RAG provides professional interview questions based on position
echo 5. Qwen-Omni Realtime processes video and audio for AI responses
echo.
echo [NOTE] System only supports video interview mode
echo        No text or voice-only interview modes available
echo.
echo Opening frontend in browser...
start "" http://localhost:5173

echo.
echo Press any key to keep this window open...
pause >nul