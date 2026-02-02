#!/usr/bin/env python3
"""
手动测试脚本 - 直接使用 MCP 工具发送消息
"""
import sys
from pathlib import Path

# 设置控制台输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from utils import create_telegram_utils

# 初始化 Telegram 工具
TELEGRAM_ENV_FILE = Path(__file__).parent / '.env'
tg = create_telegram_utils(TELEGRAM_ENV_FILE)

# 你的 Chat ID
CHAT_ID = 751182377

# 发送测试消息
message = """测试消息 - 手动发送

这是一条测试消息，用于验证 Telegram 发送功能是否正常。

如果你收到这条消息，说明：
1. ✅ Telegram Bot Token 配置正确
2. ✅ Chat ID 正确
3. ✅ 发送功能正常

时间戳: 2026-02-02 18:20"""

print(f"正在发送测试消息到 Chat ID: {CHAT_ID}")
print(f"消息内容:\n{message}\n")

success = tg.send_message(CHAT_ID, message)

if success:
    print("✅ 消息发送成功！")
    print("请检查你的 Telegram 是否收到消息。")
else:
    print("❌ 消息发送失败！")
    print("请检查 Bot Token 和 Chat ID 是否正确。")
