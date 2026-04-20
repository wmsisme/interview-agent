@echo off
chcp 65001 >nul
title AI Video Interview System - Install Dependencies (Qwen-Omni + RAG)

echo ========================================
echo   AI Video Interview System - Install Dependencies
echo ========================================
echo   Core Features: Qwen-Omni Realtime Video + RAG Enhancement
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
set MYSQL_AVAILABLE=0

echo [Step 1/6] Checking required software...
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

:: Check MySQL installation and connectivity
echo.
echo [Step 1.5/6] Checking MySQL installation and connectivity...
echo.
where mysql >nul 2>&1
if errorlevel 1 (
    echo [WARNING] MySQL client not found in PATH
    echo MySQL Server or client is required for the database
    echo.
    echo You can:
    echo 1. Install MySQL Server: https://dev.mysql.com/downloads/mysql/
    echo 2. OR Use XAMPP: https://www.apachefriends.org/
    echo 3. OR Use Docker: docker run --name mysql -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -d mysql:8.0
    echo.
    echo [IMPORTANT] Please install MySQL and ensure it's running on port 3306
    echo The system will still install, but database functionality will not work
    echo.
    choice /c yn /m "Continue installation without MySQL? (y/n): "
    if errorlevel 2 (
        echo Installation cancelled
        pause
        exit /b 1
    )
    echo [INFO] Continuing installation without MySQL verification
    set MYSQL_AVAILABLE=0
) else (
    echo [OK] MySQL client found
    echo Testing MySQL connection...
    :: Try to connect to MySQL with default credentials (root/123456)
    mysql --host=localhost --port=3306 --user=root --password=123456 --execute="SELECT 1;" > nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Cannot connect to MySQL with default credentials (root/123456)
        echo Please ensure MySQL is running and update credentials in backend\flask-backend\.env
        echo.
        echo You can test connection manually with:
        echo mysql --host=localhost --port=3306 --user=root --password=your_password
        echo.
        set MYSQL_AVAILABLE=0
    ) else (
        echo [OK] MySQL connection successful with default credentials
        :: Check if database exists
        mysql --host=localhost --port=3306 --user=root --password=123456 --execute="SHOW DATABASES LIKE 'ai_interview';" | findstr "ai_interview" > nul
        if errorlevel 1 (
            echo [INFO] Database 'ai_interview' does not exist yet
            echo It will be created when you run the application for the first time
        ) else (
            echo [OK] Database 'ai_interview' exists
        )
        set MYSQL_AVAILABLE=1
    )
)

echo [Step 2/6] Setting up Python virtual environment...
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
echo [Step 3/6] Installing Flask Backend dependencies...
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
echo [Step 4/6] Installing Frontend dependencies...
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
echo [Step 5/6] Setting up environment configuration...
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
            echo # Video Chat Configuration (Qwen-Omni Realtime)
            echo VIDEO_CHAT_API_KEY=your-qwen-omni-api-key-here
            echo VIDEO_CHAT_MODEL=qwen3.5-omni-plus-realtime
            echo VIDEO_CHAT_REGION=cn
            echo VIDEO_CHAT_VOICE=Ethan
            echo VIDEO_CHAT_ENABLED=true
            echo VIDEO_CHAT_SAMPLE_RATE=16000
            echo VIDEO_CHAT_AUDIO_CHUNK_SIZE=800
            echo VIDEO_CHAT_MAX_IMAGE_SIZE=512000
            echo VIDEO_CHAT_IMAGE_FORMAT=JPEG
            echo VIDEO_CHAT_IMAGE_QUALITY=85
            echo VIDEO_CHAT_FPS=1
            echo.
            echo # RAG Configuration (for interview question enhancement)
            echo RAG_ENABLED=true
            echo RAG_MODE=local
            echo RAG_TOP_K=5
            echo RAG_SERVICE_URL=http://localhost:8083
            echo CHROMA_DB_PATH=..\\..\\chroma_db
            echo EMBEDDING_MODEL_PATH=..\\..\\models\\bge-large-zh
            echo.
            echo # LLM Configuration (for question generation)
            echo LLM_PROVIDER=tongyi
            echo LLM_API_KEY=your-qwen-api-key-here
            echo TONGYI_MODEL=qwen-plus
        ) > .env
        echo [INFO] Created basic .env file. Please configure VIDEO_CHAT_API_KEY before running.
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
echo [Step 6/6] Verifying installation and connectivity...
echo.

:: Verify Python packages
echo Verifying Python package installation...
cd /d "%PROJECT_ROOT%backend\flask-backend"
call venv\Scripts\activate.bat
echo Testing key Python imports...
python -c "import flask; import flask_cors; import flask_sqlalchemy; import pymysql; import dashscope; import chromadb; import sentence_transformers; print('[OK] Key Python packages imported successfully')" 2>nul
if errorlevel 1 (
    echo [WARNING] Some Python packages failed to import
    echo This may cause runtime errors
    echo Try manual installation: pip install -r requirements.txt
)

:: Verify Node.js packages
echo Verifying Node.js package installation...
cd /d "%PROJECT_ROOT%frontend"
echo Checking npm package dependencies...
npm list --depth=0 2>nul | findstr /c:"UNMET DEPENDENCY" >nul
if not errorlevel 1 (
    echo [WARNING] Some npm dependencies are unmet
    echo Try: npm install
) else (
    echo [OK] npm dependencies verified
)

:: Check port availability
echo Checking port availability...
netstat -an | findstr ":8083" >nul
if not errorlevel 1 (
    echo [WARNING] Port 8083 is in use (Flask backend)
    echo You may need to change port in run.py or .env
)
netstat -an | findstr ":5173" >nul
if not errorlevel 1 (
    echo [WARNING] Port 5173 is in use (Frontend dev server)
    echo You may need to change port in vite.config.ts
)

:: Test database connectivity if MySQL is available
if "%MYSQL_AVAILABLE%"=="1" (
    echo Testing database connectivity...
    cd /d "%PROJECT_ROOT%backend\flask-backend"
    :: Create a temporary Python script for database test
    (
        echo import os
        echo import sys
        echo sys.path.insert(0, '.')
        echo try:
        echo     from app import create_app
        echo     app = create_app()
        echo     with app.app_context():
        echo         from app.models import db
        echo         db.engine.execute('SELECT 1')
        echo         print('[OK] Database connection successful')
        echo except Exception as e:
        echo     print('[WARNING] Database connection failed:', str(e))
        echo     sys.exit(1)
    ) > test_db_connectivity.py
    python test_db_connectivity.py 2>nul
    if errorlevel 1 (
        echo [WARNING] Database connectivity test failed
    )
    del test_db_connectivity.py 2>nul
)

:: Deactivate virtual environment
call deactivate >nul 2>&1

echo.
echo [OK] Installation verification completed!
echo.
echo ========================================
echo INSTALLATION COMPLETED SUCCESSFULLY!
echo ========================================
echo   AI Video Interview System Ready
echo   Core Features: Qwen-Omni Realtime Video + RAG Enhancement
echo ========================================
echo.
echo [IMPORTANT] Next steps to run the system:
echo.
echo 1. Database Setup:
echo    - Install MySQL Server if not installed
echo    - Create database: CREATE DATABASE ai_interview;
echo    - Update backend\\flask-backend\\.env with your database credentials
echo.
echo 2. Configure Qwen-Omni API for Video Interview:
echo    - Get API key from https://dashscope.aliyuncs.com/
echo    - Update VIDEO_CHAT_API_KEY in backend\\flask-backend\\.env
echo    - Note: RAG is enabled by default with local mode for interview question enhancement
echo    - ChromaDB vector database is at: ..\\..\\chroma_db
echo    - LLM (Tongyi/Qwen) is configured for question generation
echo.
echo 3. Start Flask Backend (Video Interview + RAG):
echo    cd backend\\flask-backend
echo    venv\\Scripts\\activate
echo    python run.py
echo    (Runs on http://localhost:8083)
echo.
echo 4. Start Frontend (Video Interview Interface):
echo    cd frontend
echo    npm run dev
echo    (Runs on http://localhost:5173 or available port)
echo.
echo 5. Access the Video Interview Application:
echo    Open browser and navigate to: http://localhost:5173
echo    Select a position and start video interview
echo    System will use camera and microphone for real-time interview
echo.
echo 6. Optional - Use start_fixed.bat for automatic startup:
echo    Run start_fixed.bat in project root to start all services at once
echo.
echo [SYSTEM FEATURES]
echo - Real-time video interview with Qwen-Omni multimodal AI
echo - RAG enhancement for professional interview questions
echo - Automatic question generation and evaluation
echo - No text/voice-only modes - only video interview supported
echo.
echo [TROUBLESHOOTING]
echo - If ports are in use, change port numbers in respective config files
echo - Check all services are running: Backend (8083), Frontend (5173)
echo - Ensure VIDEO_CHAT_API_KEY is configured in .env file for video interview
echo - If dashscope installation fails, use: pip install dashscope^>=1.23.9 -i https://pypi.org/simple
echo - Video interview requires camera and microphone permissions
echo.
echo ========================================
echo.
pause