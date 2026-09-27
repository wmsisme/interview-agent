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

set MYSQL_AVAILABLE=0

echo [2/3] Checking configuration and environment...
echo.

:: Check MySQL connectivity
echo Checking MySQL connectivity...
where mysql >nul 2>&1
if errorlevel 1 goto mysql_not_found

echo Testing MySQL connection with default credentials...
mysql --host=localhost --port=3306 --user=root --password=123456 --execute="SELECT 1;" > nul 2>&1
if errorlevel 1 goto mysql_connect_failed

echo [OK] MySQL connection successful
set MYSQL_AVAILABLE=1
REM Check if database exists
mysql --host=localhost --port=3306 --user=root --password=123456 --execute="SHOW DATABASES LIKE 'ai_interview';" > "%TEMP%\mysql_check.tmp" 2>&1
findstr "ai_interview" "%TEMP%\mysql_check.tmp" > nul
if errorlevel 1 (
    echo [INFO] Database 'ai_interview' does not exist yet
    echo It will be created when Flask backend starts
) else (
    echo [OK] Database 'ai_interview' exists
)
del "%TEMP%\mysql_check.tmp" >nul 2>&1
goto mysql_check_done

:mysql_not_found
set MYSQL_AVAILABLE=0
echo [WARNING] MySQL client not found in PATH
echo Database functionality may be limited
echo Install MySQL if needed for full functionality
goto mysql_check_done

:mysql_connect_failed
set MYSQL_AVAILABLE=0
echo [WARNING] Cannot connect to MySQL with default credentials (root/123456)
echo Please update database credentials in backend\flask-backend\.env if different
echo.

:mysql_check_done

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
    :: Check if database password is still default
    findstr /i "DB_PASSWORD=123456" .env | findstr /v "^#" > nul
    if not errorlevel 1 (
        echo [WARNING] DB_PASSWORD is using default value (123456)
        echo Consider changing it for security reasons
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

echo [INFO] Checking and cleaning port 8083 (Flask backend)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8083" ^| findstr "LISTENING"') do (
    echo   Found process PID %%p occupying port 8083
    taskkill /PID %%p /F >nul 2>&1
    if !errorlevel! EQU 0 (
        echo   [OK] Process %%p terminated
    ) else (
        echo   [WARNING] Failed to terminate process %%p
    )
    timeout /t 1 /nobreak >nul
)

echo [3.1] Starting Flask Backend Service (Video Interview + RAG)...
if not exist "%PROJECT_ROOT%backend\flask-backend\requirements.txt" (
    echo [ERROR] Flask backend not found at: %PROJECT_ROOT%backend\flask-backend\
    echo Please ensure Flask backend is properly set up
    pause
    exit /b 1
)
set VENV_PATH=
if exist "%PROJECT_ROOT%backend\flask-backend\venv\Scripts\activate.bat" (
    set VENV_PATH=venv
) else if exist "%PROJECT_ROOT%backend\flask-backend\.venv\Scripts\activate.bat" (
    set VENV_PATH=.venv
)

if not "!VENV_PATH!"=="" (
    echo [INFO] Using Python virtual environment ^(!VENV_PATH!^)
    set "PYTHON_EXE=%PROJECT_ROOT%backend\flask-backend\!VENV_PATH!\Scripts\python.exe"
) else (
    echo [WARNING] No virtual environment found, using system Python
    echo [NOTE] Virtual environment recommended for dependency isolation
    set PYTHON_EXE=python
)

echo [INFO] Starting Flask backend with: !PYTHON_EXE!
echo [INFO] Backend will load AI models (sentence-transformers), please wait 30-45 seconds...
echo.
start "Flask Backend (Video Interview + RAG)" /D "%PROJECT_ROOT%backend\flask-backend" !PYTHON_EXE! run.py

echo Waiting for backend to initialize (loading AI models)...
set VERIFY_ATTEMPTS=0
set VERIFY_MAX_ATTEMPTS=8
:verify_backend
set /a VERIFY_ATTEMPTS+=1
if !VERIFY_ATTEMPTS! GEQ 2 (
    echo   Checking ^(!VERIFY_ATTEMPTS!/!VERIFY_MAX_ATTEMPTS!^) - models may still be loading...
)
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8083/api/health' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Flask backend is running and healthy
    goto backend_verified
)
if !VERIFY_ATTEMPTS! GEQ !VERIFY_MAX_ATTEMPTS! (
    echo.
    echo ========================================
    echo [WARNING] Backend health check timed out
    echo ========================================
    echo This may be because:
    echo   1. AI models ^(sentence-transformers^) are still loading - wait 10 more seconds then refresh
    echo   2. Python environment is missing dependencies - check the backend terminal window
    echo   3. Port 8083 is occupied by another process
    echo.
    echo The backend terminal window should still be open - check it for error messages.
    echo If the window closed immediately, there may be a Python/dependency issue.
    echo.
    echo Press any key to continue ^(backend may still be loading in background^)...
    pause >nul
    goto backend_failed
)
timeout /t 5 /nobreak >nul
goto verify_backend
:backend_verified
:backend_failed

:: Clean up port conflicts before starting frontend
echo [INFO] Checking and cleaning port conflicts...
echo Checking port 5173 (frontend)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo   Found process PID %%p occupying port 5173
    taskkill /PID %%p /F >nul 2>&1
    if !errorlevel! EQU 0 (
        echo   [OK] Process %%p terminated
    ) else (
        echo   [WARNING] Failed to terminate process %%p
    )
    timeout /t 1 /nobreak >nul
)

echo Checking port 5174 (alternative frontend port)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5174" ^| findstr "LISTENING"') do (
    echo   Found process PID %%p occupying port 5174
    taskkill /PID %%p /F >nul 2>&1
    if !errorlevel! EQU 0 (
        echo   [OK] Process %%p terminated
    ) else (
        echo   [WARNING] Failed to terminate process %%p
    )
    timeout /t 1 /nobreak >nul
)

echo [INFO] Port cleanup completed
echo.

echo [3.2] Starting Frontend Service (Video Interview Interface)...
if not exist "%PROJECT_ROOT%frontend\package.json" (
    echo [ERROR] Frontend not found at: %PROJECT_ROOT%frontend\
    echo Please ensure frontend is properly set up
    pause
    exit /b 1
)
start "" /D "%PROJECT_ROOT%frontend" cmd /k "title Frontend Service (Video Interview) && npm run dev"
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