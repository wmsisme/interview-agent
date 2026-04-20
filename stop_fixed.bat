@echo off
chcp 65001 >nul
title AI Video Interview System - Stop (Qwen-Omni Realtime Video + RAG)

echo ========================================
echo       AI Video Interview System - Stop
echo ========================================
echo   Core Features: Qwen-Omni Realtime Video + RAG Enhancement
echo ========================================
echo.

echo [INFO] Stopping all services...
echo.

echo Stopping Python services (Flask Backend with Video Interview + RAG)...
taskkill /im python.exe 2>nul
if not errorlevel 1 (
    echo [INFO] Sent termination signal to Python processes, waiting for graceful shutdown...
    timeout /t 5 /nobreak >nul
)
taskkill /f /im python.exe 2>nul
if errorlevel 1 (
    echo [INFO] Python services (Flask Backend) not running
) else (
    echo [DONE] Python services (Flask Backend with Video Interview + RAG) stopped
)

echo Stopping Java services (legacy)...
taskkill /im java.exe 2>nul
if not errorlevel 1 (
    echo [INFO] Sent termination signal to Java processes, waiting for graceful shutdown...
    timeout /t 3 /nobreak >nul
)
taskkill /f /im java.exe 2>nul
if errorlevel 1 (
    echo [INFO] Java services (legacy) not running
) else (
    echo [DONE] Java services (legacy) stopped
)

echo Stopping Frontend Service (Video Interview Interface)...
taskkill /im node.exe 2>nul
if not errorlevel 1 (
    echo [INFO] Sent termination signal to Node.js processes, waiting for graceful shutdown...
    timeout /t 3 /nobreak >nul
)
taskkill /f /im node.exe 2>nul
if errorlevel 1 (
    echo [INFO] Frontend Service (Video Interview) not running
) else (
    echo [DONE] Frontend Service (Video Interview) stopped
)

echo.
echo ========================================
echo All services stopped - Video Interview System Shutdown
echo ========================================
echo.
echo [NOTE] Services stopped:
echo - Flask Backend (Video Interview API + RAG Enhancement)
echo - Vue.js Frontend (Video Interview Interface)
echo - RAG Service (local chroma_db for interview questions)
echo - Qwen-Omni Realtime Video Processing
echo - Any legacy services (Java, etc.)
echo.
echo To restart video interview system, run start_fixed.bat
echo.
pause