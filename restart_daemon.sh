#!/bin/bash
# Telegram-Claude Dispatcher 重启脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🔄 重启 Telegram-Claude Dispatcher"
echo "=========================================="

# 停止服务
if [ -f "dispatcher.pid" ]; then
    echo "📤 停止当前服务..."
    ./stop_daemon.sh
    sleep 2
fi

# 启动服务
echo "📦 启动新服务..."
./start_daemon.sh

echo "=========================================="
