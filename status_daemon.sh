#!/bin/bash
# Telegram-Claude Dispatcher 状态查看脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="dispatcher.pid"
LOG_FILE="dispatcher.log"

echo "=========================================="
echo "📊 Telegram-Claude Dispatcher 状态"
echo "=========================================="

# 检查 PID 文件
if [ ! -f "$PID_FILE" ]; then
    echo "状态: ❌ 未运行"
    echo "=========================================="
    exit 1
fi

# 读取 PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "状态: ❌ 未运行（PID 文件存在但进程不存在）"
    echo "建议: 运行 ./stop_daemon.sh 清理"
    echo "=========================================="
    exit 1
fi

# 获取进程信息
echo "状态: ✅ 运行中"
echo "PID: $PID"

# 获取运行时间
if command -v ps &> /dev/null; then
    ELAPSED=$(ps -p "$PID" -o etime= 2>/dev/null | tr -d ' ')
    if [ -n "$ELAPSED" ]; then
        echo "运行时间: $ELAPSED"
    fi
fi

# 获取内存使用
if command -v ps &> /dev/null; then
    MEM=$(ps -p "$PID" -o rss= 2>/dev/null | tr -d ' ')
    if [ -n "$MEM" ]; then
        MEM_MB=$((MEM / 1024))
        echo "内存使用: ${MEM_MB} MB"
    fi
fi

# 日志文件信息
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
    echo "日志文件: $LOG_FILE ($LOG_SIZE)"
    echo ""
    echo "最近日志（最后10行）:"
    echo "----------------------------------------"
    tail -10 "$LOG_FILE"
fi

echo "=========================================="
echo ""
echo "命令:"
echo "  查看实时日志: tail -f $LOG_FILE"
echo "  停止服务: ./stop_daemon.sh"
echo "  重启服务: ./restart_daemon.sh"


