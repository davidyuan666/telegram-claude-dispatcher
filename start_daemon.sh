#!/bin/bash
# Telegram-Claude Dispatcher 后台启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置
LOG_FILE="dispatcher.log"
PID_FILE="dispatcher.pid"

echo "=========================================="
echo "🚀 启动 Telegram-Claude Dispatcher"
echo "=========================================="

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "❌ Dispatcher 已经在运行 (PID: $OLD_PID)"
        echo "   如需重启，请先运行: ./stop_daemon.sh"
        exit 1
    else
        echo "⚠️  发现旧的 PID 文件，清理中..."
        rm -f "$PID_FILE"
    fi
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ 未找到 .env 文件"
    echo "   请复制 .env.example 并配置："
    echo "   cp .env.example .env"
    exit 1
fi

# 启动 dispatcher
echo "📦 启动 Dispatcher（后台模式）..."
nohup python3 dispatcher.py > "$LOG_FILE" 2>&1 &
PID=$!

# 保存 PID
echo "$PID" > "$PID_FILE"

# 等待启动
sleep 2

# 检查是否成功启动
if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Dispatcher 启动成功！"
    echo "   PID: $PID"
    echo "   日志: $LOG_FILE"
    echo ""
    echo "查看日志: tail -f $LOG_FILE"
    echo "停止服务: ./stop_daemon.sh"
    echo "查看状态: ./status_daemon.sh"
else
    echo "❌ 启动失败，请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

echo "=========================================="

