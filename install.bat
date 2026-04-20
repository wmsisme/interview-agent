@echo off
chcp 65001 >nul
title AI Interview System - Install Dependencies

echo ========================================
echo   AI Interview System - Install Dependencies
echo ========================================
echo.

set PROJECT_ROOT=%~dp0

echo [Step 1/5] Checking required software...
echo.

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.10 or higher (required for dashscope)
    echo Download: https://www.python.org/downloads/
    echo.
    echo Installation steps:
    echo 1. Download Python installer
    echo 2. During installation, CHECK \"Add Python to PATH\"
    echo 3. Restart terminal after installation
    echo.
    pause
    exit /b 1
) else (
    python --version
    echo [OK] Python found
)

:: Check pip
where pip >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found in PATH
    echo pip should be installed with Python
    echo Try reinstalling Python with \"Add Python to PATH\" checked
    echo.
    pause
    exit /b 1
) else (
    pip --version
    echo [OK] pip found
)

:: Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found in PATH
    echo Please install Node.js ^>=20.19.0 or ^>=22.12.0
    echo Download: https://nodejs.org/
    echo.
    echo Recommended: Download LTS version (Long Term Support)
    echo.
    pause
    exit /b 1
) else (
    node --version
    echo [OK] Node.js found
)

:: Check npm
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found in PATH
    echo npm should be installed with Node.js
    echo Try reinstalling Node.js
    echo.
    pause
    exit /b 1
) else (
    npm --version
    echo [OK] npm found
)

:: Optional: Check MySQL/MySQL Workbench (informational only)
echo.
echo [INFO] Database requirements:
echo - MySQL Server 5.7 or higher (or MariaDB 10.2 or higher)
echo - Database client (MySQL Workbench, phpMyAdmin, or command line)
echo.
echo If you don't have MySQL installed, you can:
echo 1. Install MySQL Server: https://dev.mysql.com/downloads/mysql/
echo 2. OR Use XAMPP: https://www.apachefriends.org/
echo 3. OR Use Docker: docker run --name mysql -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -d mysql:8.0
echo.

echo [Step 2/5] Setting up Python virtual environment...
echo.
cd /d \"%PROJECT_ROOT%backend\\flask-backend\"
if not exist \"venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo Make sure Python is correctly installed
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

echo.
echo [Step 3/5] Installing Flask Backend dependencies...
echo.
cd /d \"%PROJECT_ROOT%backend\\flask-backend\"
echo Activating virtual environment and installing dependencies...
call venv\\Scripts\\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing...
)

echo Installing Flask backend dependencies...
echo Note: Includes dashscope for Qwen-Omni API integration
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Flask backend dependencies
    echo Please check requirements.txt file
    echo If dashscope installation fails, try: pip install dashscope^>=1.23.9 -i https://pypi.org/simple
    pause
    exit /b 1
)
echo [OK] Flask backend dependencies installed

:: Deactivate virtual environment for other operations
call deactivate >nul 2>&1

echo.
echo [Step 4/5] Installing Frontend dependencies...
echo.
cd /d \"%PROJECT_ROOT%frontend\"
echo Installing Node.js dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    echo Please check your Node.js installation
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed

echo.
echo [Step 5/5] Setting up environment configuration...
echo.
echo Creating environment configuration files if they don't exist...

:: Create .env file for Flask backend if it doesn't exist
cd /d \"%PROJECT_ROOT%backend\\flask-backend\"
if not exist \".env\" (
    echo Creating .env file from example...
    if exist \".env.example\" (
        copy \".env.example\" \".env\" >nul
        echo [INFO] Created .env file. Please edit it to configure database connection.
    ) else (
        echo [INFO] No .env.example found. Creating basic .env file...
        (
            echo # Flask Backend Configuration
            echo FLASK_APP=app
            echo FLASK_ENV=development
            echo FLASK_DEBUG=True
            echo SECRET_KEY=your-secret-key-change-this
            echo.
            echo # Database Configuration
            echo DB_HOST=localhost
            echo DB_PORT=3306
            echo DB_NAME=ai_interview
            echo DB_USER=root
            echo DB_PASSWORD=123456
            echo.
            echo # Qwen-Omni Configuration
            echo QWEN_OMNI_API_KEY=your-qwen-api-key-here
            echo QWEN_OMNI_MODEL=qwen3.5-omni-flash-realtime
            echo QWEN_OMNI_WS_URL=wss://dashscope.aliyuncs.com/api-ws/v1/realtime
            echo QWEN_OMNI_VOICE=Cherry
            echo QWEN_OMNI_ENABLED=true
            echo.
            echo # RAG Configuration
            echo RAG_ENABLED=true
            echo RAG_MODE=local
            echo RAG_TOP_K=5
            echo CHROMA_DB_PATH=..\\..\\chroma_db
            echo EMBEDDING_MODEL_PATH=..\\..\\models\\bge-large-zh
        ) > .env
        echo [INFO] Created basic .env file. Please configure QWEN_OMNI_API_KEY before running.
    )
) else (
    echo [INFO] .env file already exists
)

:: Create .env.development for frontend if it doesn't exist
cd /d \"%PROJECT_ROOT%frontend\"
if not exist \".env.development\" (
    echo Creating frontend environment file...
    (
        echo VITE_API_BASE_URL=http://localhost:8083/api
        echo VITE_WS_BASE_URL=ws://localhost:8083
        echo VITE_APP_TITLE=AI模拟面试教练 (Qwen-Omni集成版)
    ) > .env.development
    echo [OK] Frontend environment file created
) else (
    echo [INFO] Frontend environment file already exists
)

echo.
echo ========================================
echo INSTALLATION COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo [IMPORTANT] Next steps to run the system:
echo.
echo 1. Database Setup:
echo    - Install MySQL Server if not installed
echo    - Create database: CREATE DATABASE ai_interview;
echo    - Update backend\\flask-backend\\.env with your database credentials
echo.
echo 2. Configure Qwen-Omni API:
echo    - Get API key from https://dashscope.aliyuncs.com/
echo    - Update QWEN_OMNI_API_KEY in backend\\flask-backend\\.env
echo    - Note: RAG is enabled by default with local mode (RAG_ENABLED=true, RAG_MODE=local)
echo    - ChromaDB vector database is at: ..\\..\\chroma_db
echo.
echo 3. Start Flask Backend:
echo    cd backend\\flask-backend
echo    venv\\Scripts\\activate
echo    python run.py
echo    (Runs on http://localhost:8083)
echo.
echo 4. Start Frontend:
echo    cd frontend
echo    npm run dev
echo    (Runs on http://localhost:5173 or available port)
echo.
echo 5. Access the application:
echo    Open browser and navigate to: http://localhost:5173
echo    Choose \"Qwen-Omni面试\" for real-time multimodal interview
echo.
echo 6. Optional - Use start_fixed.bat for automatic startup:
echo    Run start_fixed.bat in project root to start all services at once
echo.
echo [TROUBLESHOOTING]
echo - If ports are in use, change port numbers in respective config files
echo - Check all services are running: Backend (8083), Frontend (5173)
echo - Ensure Qwen-Omni API key is configured in .env file
echo - If dashscope installation fails, use: pip install dashscope^>=1.23.9 -i https://pypi.org/simple
echo.
echo ========================================
echo.
pause