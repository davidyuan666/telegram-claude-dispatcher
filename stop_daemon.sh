#!/bin/bash
# Telegram-Claude Dispatcher 停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="dispatcher.pid"

echo "=========================================="
echo "🛑 停止 Telegram-Claude Dispatcher"
echo "=========================================="

# 检查 PID 文件
if [ ! -f "$PID_FILE" ]; then
    echo "❌ 未找到 PID 文件，Dispatcher 可能未运行"
    exit 1
fi

# 读取 PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  进程不存在 (PID: $PID)"
    rm -f "$PID_FILE"
    exit 1
fi

# 停止进程
echo "📤 发送停止信号到进程 $PID..."
kill "$PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Dispatcher 已停止"
        rm -f "$PID_FILE"
        echo "=========================================="
        exit 0
    fi
    sleep 1
done

# 强制停止
echo "⚠️  进程未响应，强制停止..."
kill -9 "$PID"
sleep 1

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Dispatcher 已强制停止"
    rm -f "$PID_FILE"
else
    echo "❌ 无法停止进程"
    exit 1
fi

echo "=========================================="
