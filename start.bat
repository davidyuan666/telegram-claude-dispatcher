@echo off
chcp 65001 > nul
echo ========================================
echo Telegram Claude Dispatcher
echo ========================================
echo.

cd /d %~dp0

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动调度器
python dispatcher.py

pause
