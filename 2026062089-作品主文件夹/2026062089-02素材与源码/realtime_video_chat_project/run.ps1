# 实时视频对话项目 - PowerShell启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   实时视频对话项目 - 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python环境检测通过: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未检测到Python，请先安装Python 3.8或更高版本" -ForegroundColor Red
    Write-Host "下载地址：https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 检查依赖是否安装
Write-Host "检查依赖包安装状态..." -ForegroundColor Gray
$dependencies = @("dashscope", "cv2", "pyaudio")
$missingDeps = @()

foreach ($dep in $dependencies) {
    try {
        python -c "import $dep" 2>&1 | Out-Null
    } catch {
        $missingDeps += $dep
    }
}

if ($missingDeps.Count -gt 0) {
    Write-Host "⚠️  检测到未安装的依赖包: $($missingDeps -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    
    $choice = Read-Host "是否安装依赖包？(Y/N)"
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        Write-Host "正在安装依赖包，这可能需要几分钟..." -ForegroundColor Yellow
        pip install -r requirements.txt
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 依赖包安装失败" -ForegroundColor Red
            Write-Host "请手动运行：pip install -r requirements.txt" -ForegroundColor Yellow
            Read-Host "按Enter键退出"
            exit 1
        }
        
        Write-Host "✅ 依赖包安装完成" -ForegroundColor Green
    } else {
        Write-Host "请手动运行以下命令安装依赖：" -ForegroundColor Yellow
        Write-Host "pip install -r requirements.txt" -ForegroundColor Cyan
        Read-Host "按Enter键退出"
        exit 1
    }
} else {
    Write-Host "✅ 所有依赖包已安装" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   启动实时视频对话程序" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请确保：" -ForegroundColor Gray
Write-Host "1. 已授予摄像头访问权限" -ForegroundColor Gray
Write-Host "2. 已授予麦克风访问权限" -ForegroundColor Gray
Write-Host "3. 网络连接正常" -ForegroundColor Gray
Write-Host ""
Write-Host "按Enter键开始运行..." -ForegroundColor Yellow
Read-Host

Write-Host ""
Write-Host "🚀 正在启动程序..." -ForegroundColor Green
Write-Host "按 Ctrl+C 或关闭窗口可退出程序" -ForegroundColor Gray
Write-Host ""

# 运行主程序
python realtime_video_chat.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 程序运行出错" -ForegroundColor Red
    Write-Host "请检查：" -ForegroundColor Yellow
    Write-Host "1. config.py 中的API配置" -ForegroundColor Gray
    Write-Host "2. 摄像头和麦克风权限" -ForegroundColor Gray
    Write-Host "3. 网络连接" -ForegroundColor Gray
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host ""
Write-Host "✅ 程序运行完成" -ForegroundColor Green
Read-Host "按Enter键退出"