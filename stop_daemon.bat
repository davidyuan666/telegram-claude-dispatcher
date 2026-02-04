@echo off
REM Telegram-Claude Dispatcher 停止脚本 (Windows)

cd /d "%~dp0"

echo ==========================================
echo 停止 Telegram-Claude Dispatcher
echo ==========================================

REM 查找并停止 Python 进程
echo 正在查找 dispatcher.py 进程...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | find "dispatcher.py" >nul
    if not errorlevel 1 (
        echo 找到进程 PID: %%i
        taskkill /PID %%i /F
        echo 成功: Dispatcher 已停止
        goto :done
    )
)

echo 警告: 未找到运行中的 Dispatcher 进程
:done
if exist "dispatcher.pid" del "dispatcher.pid"
echo ==========================================
pause
