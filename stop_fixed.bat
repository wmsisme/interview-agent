@echo off
chcp 65001 >nul
title AI Interview System - Stop (Flask + Qwen-Omni + RAG)

echo ========================================
echo       AI Interview System - Stop (Flask + Qwen-Omni + RAG)
echo ========================================
echo.

echo [INFO] Stopping all services...
echo.

taskkill /f /im python.exe 2>nul
if errorlevel 1 (
    echo [INFO] Python services (Flask Backend) not running
) else (
    echo [DONE] Python services (Flask Backend with Qwen-Omni) stopped
)

taskkill /f /im java.exe 2>nul
if errorlevel 1 (
    echo [INFO] Java services (legacy) not running
) else (
    echo [DONE] Java services (legacy) stopped
)

taskkill /f /im node.exe 2>nul
if errorlevel 1 (
    echo [INFO] Frontend Service not running
) else (
    echo [DONE] Frontend Service stopped
)

echo.
echo ========================================
echo All services stopped (Flask, Frontend, Qwen-Omni, RAG)
echo ========================================
echo.
echo [NOTE] Services stopped:
echo - Flask Backend (with Qwen-Omni integration)
echo - Vue.js Frontend (with Qwen-Omni interface)
echo - RAG Service (local chroma_db)
echo - Any legacy Java services
echo.
echo To restart, run start_fixed.bat
echo.
pause