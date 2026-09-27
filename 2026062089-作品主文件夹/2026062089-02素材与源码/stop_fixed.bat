@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title AI Video Interview System - Stop (Qwen-Omni Realtime Video + RAG)

echo ========================================
echo       AI Video Interview System - Stop
echo ========================================
echo   Core Features: Qwen-Omni Realtime Video + RAG Enhancement
echo ========================================
echo.

echo [INFO] Stopping this project's services only...
echo        Matching is port- and command-line based; unrelated
echo        python / node processes are NOT touched.
echo.

set "PROJ=%~dp0"
set "PS=powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass"
set "TMPKILL=%TEMP%\stop_fixed_targets.txt"
set "PORT_STOPPED=0"

echo ------------------------------------------------------------------
echo [1/4] Stopping port occupants (8083 backend, 5173/5174 frontend)
echo ------------------------------------------------------------------
set "PORTS=8083 5173 5174"
for %%P in (%PORTS%) do (
    echo Checking port %%P ...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%%P" ^| findstr "LISTENING"') do (
        echo   Port %%P is held by PID %%p - terminating ...
        taskkill /PID %%p 2>nul
        ping -n 3 127.0.0.1 >nul
        taskkill /f /PID %%p 2>nul
        if !errorlevel! EQU 0 (
            echo   [OK] PID %%p stopped
            set "PORT_STOPPED=1"
        ) else (
            echo   [WARN] PID %%p could not be stopped - try running this file as Administrator
        )
    )
)
if "!PORT_STOPPED!"=="1" (
    echo [DONE] Port occupants handled
) else (
    echo [INFO] No service is listening on ports: %PORTS%
)

echo.
echo ------------------------------------------------------------------
echo [2/4] Python processes belonging to THIS project (flask-backend / run.py)
echo ------------------------------------------------------------------
if exist "!TMPKILL!" del "!TMPKILL!" >nul 2>&1
%PS% -Command "$dir=[regex]::Escape($args[0]);$sub=$args[1];$pat=$dir+$sub.Replace('\','\\')+'|'+$dir+'run\.py|'+$sub.Replace('\','\\')+'\\run\.py';Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { $_.CommandLine -match $pat } | ForEach-Object { if ($_.CommandLine) { $c=$_.CommandLine } else { $c='<no command line>' }; Write-Output ('{0}{1}{2}' -f $_.ProcessId, [char]9, $c) }" "!PROJ!" "backend\flask-backend" > "!TMPKILL!" 2>nul
set "FOUND=0"
if exist "!TMPKILL!" (
    for /f "usebackq tokens=1,* delims=	" %%a in ("!TMPKILL!") do (
        if not "%%a"=="" (
            set "FOUND=1"
            echo   Target PID %%a
            echo     cmdline: %%b
            taskkill /PID %%a 2>nul
            ping -n 2 127.0.0.1 >nul
            taskkill /f /PID %%a 2>nul
            if !errorlevel! EQU 0 (
                echo     [OK] PID %%a stopped
            ) else (
                echo     [WARN] PID %%a could not be stopped - try running this file as Administrator
            )
        )
    )
)
if "!FOUND!"=="0" echo [INFO] No project Python process found - nothing to clean up
if exist "!TMPKILL!" del "!TMPKILL!" >nul 2>&1

echo.
echo ------------------------------------------------------------------
echo [3/4] Node processes serving THIS project's frontend directory
echo ------------------------------------------------------------------
if exist "!TMPKILL!" del "!TMPKILL!" >nul 2>&1
%PS% -Command "$dir=[regex]::Escape($args[0]);$sub=$args[1].Replace('\','\\');$pat=$dir+$sub;Get-CimInstance Win32_Process -Filter \"name='node.exe'\" | Where-Object { $_.CommandLine -match $pat } | ForEach-Object { if ($_.CommandLine) { $c=$_.CommandLine } else { $c='<no command line>' }; Write-Output ('{0}{1}{2}' -f $_.ProcessId, [char]9, $c) }" "!PROJ!" "frontend" > "!TMPKILL!" 2>nul
set "FOUND=0"
if exist "!TMPKILL!" (
    for /f "usebackq tokens=1,* delims=	" %%a in ("!TMPKILL!") do (
        if not "%%a"=="" (
            set "FOUND=1"
            echo   Target PID %%a
            echo     cmdline: %%b
            taskkill /PID %%a 2>nul
            ping -n 2 127.0.0.1 >nul
            taskkill /f /PID %%a 2>nul
            if !errorlevel! EQU 0 (
                echo     [OK] PID %%a stopped
            ) else (
                echo     [WARN] PID %%a could not be stopped - try running this file as Administrator
            )
        )
    )
)
if "!FOUND!"=="0" echo [INFO] No project frontend Node process found - nothing to clean up
if exist "!TMPKILL!" del "!TMPKILL!" >nul 2>&1

echo.
echo ------------------------------------------------------------------
echo [4/4] Summary
echo ------------------------------------------------------------------
if "!PORT_STOPPED!"=="1" (
    echo [DONE] Frontend/Backend port occupants stopped
) else (
    echo [INFO] No port occupants needed stopping
)
echo [NOTE] Cleanup is scoped to:
echo        - listeners on ports 8083 / 5173 / 5174
echo        - python.exe whose command line contains %PROJ%backend\flask-backend
echo        - python.exe whose command line contains %PROJ%run.py
echo        - node.exe whose command line contains %PROJ%frontend
echo        Java removal was dropped - this project has no Java component.

echo.
echo ========================================
echo All services stopped - Video Interview System Shutdown
echo ========================================
echo.
echo [NOTE] Services handled:
echo - Flask Backend (Video Interview API + RAG Enhancement)
echo - Vue.js Frontend (Video Interview Interface)
echo - RAG Service (local chroma_db for interview questions)
echo - Qwen-Omni Realtime Video Processing
echo.
echo To restart video interview system, run start_fixed.bat
echo.
pause
