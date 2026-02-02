#!/usr/bin/env python3
"""
测试 Telegram Utils 模块
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import create_telegram_utils

def test_telegram_utils():
    print("=" * 60)
    print("测试 Telegram Utils 模块")
    print("=" * 60)

    # 创建实例（从 .env 文件加载配置）
    try:
        tg = create_telegram_utils('.env')
        print("[OK] Telegram Utils 初始化成功")
        print(f"   Last Update ID: {tg.last_update_id}")

        # 测试快速检查
        print("\n[测试] 快速检查...")
        has_messages = tg.check_new_messages()

        if has_messages:
            print("[发现] 有新消息！")

            # 获取消息详情
            messages = tg.get_pending_messages()
            print(f"[结果] 获取到 {len(messages)} 条消息")

            for msg in messages[:3]:
                print(f"\n消息:")
                print(f"  Chat ID: {msg['chat_id']}")
                print(f"  用户: {msg['user']['username']}")
                print(f"  内容: {msg['text'][:50]}...")
        else:
            print("[OK] 没有新消息")

        print("\n[OK] 测试完成")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_telegram_utils()
