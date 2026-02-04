@echo off
REM Telegram-Claude Dispatcher 后台启动脚本 (Windows)

cd /d "%~dp0"

set LOG_FILE=dispatcher.log
set PID_FILE=dispatcher.pid

echo ==========================================
echo 启动 Telegram-Claude Dispatcher
echo ==========================================

REM 检查是否已经在运行
if exist "%PID_FILE%" (
    set /p OLD_PID=<"%PID_FILE%"
    tasklist /FI "PID eq %OLD_PID%" 2>NUL | find /I /N "python">NUL
    if "%ERRORLEVEL%"=="0" (
        echo 错误: Dispatcher 已经在运行 (PID: %OLD_PID%^)
        echo 如需重启，请先运行: stop_daemon.bat
        pause
        exit /b 1
    ) else (
        echo 发现旧的 PID 文件，清理中...
        del "%PID_FILE%"
    )
)

REM 检查 Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到 python，请先安装 Python 3
    pause
    exit /b 1
)

REM 检查 .env 文件
if not exist ".env" (
    echo 错误: 未找到 .env 文件
    echo 请复制 .env.example 并配置
    pause
    exit /b 1
)

REM 启动 dispatcher（后台模式）
echo 启动 Dispatcher（后台模式）...
start /B python dispatcher.py > "%LOG_FILE%" 2>&1

REM 等待启动
timeout /t 2 /nobreak >nul

echo 成功: Dispatcher 已启动
echo 日志文件: %LOG_FILE%
echo.
echo 查看日志: type %LOG_FILE%
echo 停止服务: stop_daemon.bat
echo ==========================================
pause

