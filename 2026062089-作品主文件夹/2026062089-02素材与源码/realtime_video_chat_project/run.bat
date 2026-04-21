@echo off
chcp 65001 >nul
echo ========================================
echo   实时视频对话项目 - 启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检测通过
echo.

REM 检查依赖是否安装
echo 检查依赖包安装状态...
python -c "import dashscope, cv2, pyaudio" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  检测到未安装的依赖包
    echo.
    echo 是否安装依赖包？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        echo 正在安装依赖包，这可能需要几分钟...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ 依赖包安装失败
            echo 请手动运行：pip install -r requirements.txt
            pause
            exit /b 1
        )
        echo ✅ 依赖包安装完成
    ) else (
        echo 请手动运行以下命令安装依赖：
        echo pip install -r requirements.txt
        pause
        exit /b 1
    )
) else (
    echo ✅ 所有依赖包已安装
)

echo.
echo ========================================
echo   启动实时视频对话程序
echo ========================================
echo.
echo 请确保：
echo 1. 已授予摄像头访问权限
echo 2. 已授予麦克风访问权限
echo 3. 网络连接正常
echo.
echo 按任意键开始运行...
pause >nul

echo.
echo 🚀 正在启动程序...
echo 按 Ctrl+C 或关闭窗口可退出程序
echo.

REM 运行主程序
python realtime_video_chat.py

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
    echo 请检查：
    echo 1. config.py 中的API配置
    echo 2. 摄像头和麦克风权限
    echo 3. 网络连接
    pause
    exit /b 1
)

echo.
echo ✅ 程序运行完成
pause