#!/usr/bin/env python3
"""
Telegram-Claude Dispatcher - 重构版
仿照opencrawl架构：Telegram -> Dispatcher -> 无头Claude CLI -> Hook -> 返回Telegram
"""
import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from utils import create_telegram_utils
from core import MessageProcessor, PreHook, PostHook

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dispatcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置控制台输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 配置
PROJECT_DIR = Path(__file__).parent
WORKSPACE_DIR = PROJECT_DIR.parent.resolve()  # 使用父目录作为工作目录（claudecodelabspace）
TELEGRAM_ENV_FILE = PROJECT_DIR / '.env'

# 加载 .env 文件到环境变量
if TELEGRAM_ENV_FILE.exists():
    with open(TELEGRAM_ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# 从环境变量读取配置
CHECK_INTERVAL = int(os.getenv('POLLING_INTERVAL', 10))
TASK_TIMEOUT = 180  # 任务超时时间（秒）
LOCK_FILE = PROJECT_DIR / 'dispatcher.lock'
CLAUDE_CLI_PATH = os.getenv('CLAUDE_CLI_PATH', 'claude')


class TelegramClaudeDispatcher:
    """Telegram-Claude 调度器 - 重构版"""

    def __init__(self):
        """初始化调度器"""
        self.telegram_utils = None
        self.message_processor = None
        self.pre_hook = None
        self.post_hook = None
        self._init_components()

    def _init_components(self):
        """初始化各个组件"""
        try:
            # 初始化 Telegram 工具
            self.telegram_utils = create_telegram_utils(TELEGRAM_ENV_FILE)
            logger.info("✅ Telegram 工具初始化成功")

            # 初始化消息处理器（启用会话隔离）
            self.message_processor = MessageProcessor(
                workspace_dir=WORKSPACE_DIR,
                claude_cli_path=CLAUDE_CLI_PATH
            )
            logger.info("✅ 消息处理器初始化成功")

            # 初始化 PreHook（消息接收预处理）
            pre_hook_config = {
                'whitelist': [],  # 留空表示不启用白名单
                'blacklist': [],  # 可以添加黑名单用户ID
                'rate_limit': 10,  # 每分钟最多10次请求
            }
            self.pre_hook = PreHook(pre_hook_config)
            logger.info("✅ PreHook 初始化成功")

            # 初始化 PostHook（消息发送后处理）
            post_hook_config = {
                'max_length': 4000,
                'enable_formatting': True,
                'add_timestamp': False,
            }
            self.post_hook = PostHook(post_hook_config)
            logger.info("✅ PostHook 初始化成功")

        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            raise

    def acquire_lock(self):
        """获取进程锁"""
        try:
            if LOCK_FILE.exists():
                try:
                    import psutil
                    with open(LOCK_FILE, 'r') as f:
                        old_pid = int(f.read().strip())
                    if psutil.pid_exists(old_pid):
                        logger.error(f"❌ 另一个实例正在运行 (PID: {old_pid})")
                        return False
                    LOCK_FILE.unlink()
                except ImportError:
                    logger.error(f"❌ 锁文件已存在，请手动删除: {LOCK_FILE}")
                    return False

            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"✅ 已获取进程锁 (PID: {os.getpid()})")
            return True
        except Exception as e:
            logger.error(f"❌ 获取进程锁失败: {e}")
            return False

    def release_lock(self):
        """释放进程锁"""
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
                logger.info("✅ 已释放进程锁")
        except Exception as e:
            logger.error(f"❌ 释放进程锁失败: {e}")

    def check_and_process_messages(self):
        """检查并处理 Telegram 消息"""
        try:
            logger.info("=" * 60)
            logger.info("🔔 开始新的检查周期")
            logger.info("=" * 60)

            # 第一步：快速检查是否有新消息
            logger.info("📥 快速检查是否有新的 Telegram 消息...")
            check_start = time.time()

            has_messages = self.telegram_utils.check_new_messages()
            check_elapsed = time.time() - check_start
            logger.info(f"   检查耗时: {check_elapsed:.2f}秒")

            if not has_messages:
                logger.info("✅ 没有新消息")
                logger.info("💤 跳过本次处理，节省资源")
                return True

            # 第二步：获取消息详情（不标记为已读）
            logger.info("📬 发现新消息！")
            logger.info("📥 获取消息详情...")

            messages = self.telegram_utils.get_pending_messages(mark_as_read=False)
            if not messages:
                logger.warning("⚠️ 无法获取消息详情")
                return False

            logger.info(f"📊 获取到 {len(messages)} 条消息")
            for i, msg in enumerate(messages, 1):
                logger.info(f"   消息 {i}: Chat ID={msg['chat_id']}, 用户={msg['user']['username']}")
                logger.info(f"           内容: {msg['text'][:50]}...")

            # PreHook: 消息预处理
            logger.info("-" * 60)
            should_continue, quick_reply, processed_messages = self.pre_hook.process(messages)

            if not should_continue:
                # PreHook 拦截了消息，发送快速回复
                logger.info("🛑 PreHook 拦截消息，发送快速回复")
                if quick_reply:
                    for msg in messages:
                        self.telegram_utils.send_message(msg['chat_id'], quick_reply)

                # 确认消息已处理
                update_ids = [msg['update_id'] for msg in messages]
                self.telegram_utils.acknowledge_messages(update_ids)
                return True

            return self._process_messages_with_claude(processed_messages)

        except Exception as e:
            logger.error(f"❌ 检查消息失败: {e}")
            return False

    def _process_messages_with_claude(self, messages):
        """使用Claude CLI处理消息"""
        try:
            # 第三步：调用无头Claude CLI处理
            logger.info("📤 启动 Claude CLI 处理消息...")
            logger.info("-" * 60)

            start_time = time.time()
            result = self.message_processor.process_messages(messages, timeout=TASK_TIMEOUT)
            elapsed = time.time() - start_time

            logger.info("-" * 60)
            logger.info(f"⏱️  总执行时间: {elapsed:.1f}秒")
            logger.info(f"📤 返回码: {result.get('returncode', -1)}")
            logger.info(f"📊 输出长度: {len(result.get('output', ''))} 字符")
            logger.info("-" * 60)

            # 第五步：PostHook 处理输出并发送到 Telegram
            if result['success']:
                # 使用 PostHook 提取和格式化回复内容
                success, reply_content, error_msg = self.post_hook.process(
                    result.get('output', ''),
                    messages
                )

                if success and reply_content:
                    logger.info("📤 发送回复到 Telegram...")

                    # 为每条消息发送回复
                    for msg in messages:
                        chat_id = msg['chat_id']
                        if self.telegram_utils.send_message(chat_id, reply_content):
                            logger.info(f"✅ 已发送回复到 Chat ID: {chat_id}")
                        else:
                            logger.warning(f"⚠️ 发送回复失败 (Chat ID: {chat_id})")
                else:
                    logger.warning(f"⚠️ PostHook 处理失败: {error_msg}")

            logger.info("-" * 60)

            # 第六步：确认消息已处理（无论成功或失败）
            # 避免失败消息无限重试，造成资源浪费
            update_ids = [msg['update_id'] for msg in messages]

            if result['success']:
                logger.info("✅ 任务执行成功")

                # 确认消息已处理
                if self.telegram_utils.acknowledge_messages(update_ids):
                    logger.info(f"✅ 已确认 {len(messages)} 条消息处理完成")
                else:
                    logger.warning("⚠️ 确认消息失败，下次可能会重复处理")

                return True
            else:
                logger.warning(f"⚠️ 任务执行失败 (返回码: {result.get('returncode', -1)})")

                # 即使失败也确认消息，避免无限重试
                if self.telegram_utils.acknowledge_messages(update_ids):
                    logger.info(f"✅ 已确认 {len(messages)} 条消息（避免重复处理）")
                else:
                    logger.warning("⚠️ 确认消息失败")

                return False

        except Exception as e:
            logger.error(f"❌ 处理消息失败: {e}")
            return False

    def run(self):
        """主循环"""
        logger.info("=" * 60)
        logger.info("🚀 Telegram-Claude Dispatcher 启动 - 重构版")
        logger.info("=" * 60)
        logger.info(f"📁 工作目录: {WORKSPACE_DIR}")
        logger.info(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
        logger.info(f"🤖 Claude CLI: {CLAUDE_CLI_PATH}")
        logger.info(f"🔍 平台: {sys.platform}")
        logger.info(f"🔍 是否.cmd文件: {CLAUDE_CLI_PATH.endswith('.cmd')}")
        logger.info(f"🔍 将使用shell模式: {sys.platform == 'win32' and CLAUDE_CLI_PATH.endswith('.cmd')}")
        logger.info(f"🔒 无头模式: 启用（跳过权限检查）")
        logger.info(f"📦 会话隔离: 启用")
        logger.info("=" * 60)

        if not self.acquire_lock():
            logger.error("❌ 无法获取进程锁，退出")
            return

        try:
            cycle_count = 0
            start_time = time.time()

            while True:
                cycle_count += 1
                total_runtime = time.time() - start_time

                logger.info("")
                logger.info(f"🔄 第 {cycle_count} 次检查 (总运行: {total_runtime/60:.1f}分钟)")

                # 执行检查
                self.check_and_process_messages()

                # 等待下一次检查
                logger.info("")
                logger.info(f"😴 休眠 {CHECK_INTERVAL} 秒...")
                next_check = time.strftime('%H:%M:%S', time.localtime(time.time() + CHECK_INTERVAL))
                logger.info(f"   下次检查: {next_check}")
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 60)
            logger.info("🛑 收到停止信号")
            logger.info(f"📊 总检查次数: {cycle_count}")
            logger.info(f"📊 总运行时间: {(time.time() - start_time)/60:.1f}分钟")
            logger.info("=" * 60)
            self.release_lock()
        except Exception as e:
            logger.error(f"❌ 主循环出错: {e}")
            self.release_lock()


def main():
    """主入口"""
    dispatcher = TelegramClaudeDispatcher()
    dispatcher.run()


if __name__ == "__main__":
    main()
