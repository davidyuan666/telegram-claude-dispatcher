#!/usr/bin/env python3
"""
Claude CLI 调度器 - 最简版
使用 utils 模块快速检查消息，有消息才启动 Claude CLI
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from utils import create_telegram_utils

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claude_dispatcher_simple.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置控制台输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 配置
WORKSPACE_DIR = r'C:\workspace\claudecodelabspace'
CHECK_INTERVAL = 30  # 检查间隔（秒）
LOCK_FILE = r'C:\workspace\claudecodelabspace\dispatcher_simple.lock'
TELEGRAM_ENV_FILE = r'C:\workspace\claudecodelabspace\mcps\TelegramReceiverMCP\.env'


class ClaudeDispatcherSimple:
    """最简版 Claude CLI 调度器 - 使用 utils 快速检查"""

    def __init__(self):
        self.lock_file_handle = None
        self.telegram_utils = None
        self._init_telegram_utils()

    def _init_telegram_utils(self):
        """初始化 Telegram 工具"""
        try:
            self.telegram_utils = create_telegram_utils(TELEGRAM_ENV_FILE)
            logger.info("✅ Telegram 工具初始化成功")
        except Exception as e:
            logger.error(f"❌ Telegram 工具初始化失败: {e}")
            self.telegram_utils = None

    def acquire_lock(self):
        """获取进程锁"""
        try:
            if Path(LOCK_FILE).exists():
                try:
                    import psutil
                    with open(LOCK_FILE, 'r') as f:
                        old_pid = int(f.read().strip())
                    if psutil.pid_exists(old_pid):
                        logger.error(f"❌ 另一个实例正在运行 (PID: {old_pid})")
                        return False
                    Path(LOCK_FILE).unlink()
                except ImportError:
                    logger.error("❌ 锁文件已存在，请手动删除: " + LOCK_FILE)
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
            if Path(LOCK_FILE).exists():
                Path(LOCK_FILE).unlink()
                logger.info("✅ 已释放进程锁")
        except Exception as e:
            logger.error(f"❌ 释放进程锁失败: {e}")

    def check_and_process_messages(self):
        """检查并处理 Telegram 消息 - 使用 utils 快速检查，有消息才启动 Claude CLI"""
        try:
            logger.info("=" * 60)
            logger.info("🔔 开始新的检查周期")
            logger.info("=" * 60)

            # 第一步：使用 utils 快速检查（不启动 Claude CLI）
            logger.info("📥 快速检查是否有新的 Telegram 消息...")
            check_start = time.time()

            if self.telegram_utils:
                has_messages = self.telegram_utils.check_new_messages()
                check_elapsed = time.time() - check_start
                logger.info(f"   检查耗时: {check_elapsed:.2f}秒")
            else:
                logger.warning("⚠️ Telegram 工具未初始化，将启动 Claude CLI 检查")
                has_messages = True

            if not has_messages:
                logger.info("✅ 没有新消息")
                logger.info("💤 跳过本次处理，节省资源")
                return True

            # 第二步：有新消息，启动 Claude CLI 处理
            logger.info("📬 发现新消息！")
            logger.info("📤 启动 Claude CLI 处理消息...")
            logger.info("-" * 60)

            # 创建提示词
            prompt = """请处理新的 Telegram 消息。

【工作流程】
1. 使用 mcp__telegram-receiver__check_pending_messages 获取新消息
2. 理解用户的需求
3. 生成合适的回复
4. 使用 mcp__telegram-sender__send_telegram_message 发送回复
5. 如果需要，使用其他 MCP 工具（arxiv搜索、12306查询等）

完成后输出 "TASK_COMPLETE"。
"""

            # 启动 Claude CLI 进程
            start_time = time.time()
            logger.info("🚀 正在启动 Claude CLI...")

            # 使用 Popen 以便实时显示输出
            process = subprocess.Popen(
                ['claude', '--dangerously-skip-permissions', prompt],
                cwd=WORKSPACE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                shell=True
            )

            logger.info(f"✅ Claude CLI 已启动 (PID: {process.pid})")
            logger.info("📊 开始监控执行进度...")
            logger.info("-" * 60)

            # 实时读取输出
            output_lines = []
            error_lines = []
            line_count = 0
            last_progress_time = time.time()

            try:
                # 等待进程完成，同时读取输出
                while True:
                    # 检查进程是否结束
                    if process.poll() is not None:
                        break

                    # 检查是否超时
                    elapsed = time.time() - start_time
                    if elapsed > 120:  # 2分钟超时
                        logger.error("❌ 执行超时（120秒），强制终止")
                        process.kill()
                        break

                    # 每10秒显示一次进度
                    if time.time() - last_progress_time > 10:
                        logger.info(f"⏳ 执行中... 已用时 {elapsed:.0f}秒")
                        last_progress_time = time.time()

                    time.sleep(1)

                # 读取所有剩余输出
                stdout, stderr = process.communicate(timeout=5)
                if stdout:
                    output_lines = stdout.split('\n')
                if stderr:
                    error_lines = stderr.split('\n')

            except subprocess.TimeoutExpired:
                logger.error("❌ 读取输出超时")
                process.kill()
                stdout, stderr = process.communicate()
                if stdout:
                    output_lines = stdout.split('\n')
                if stderr:
                    error_lines = stderr.split('\n')

            elapsed = time.time() - start_time
            logger.info("-" * 60)
            logger.info(f"🔒 Claude CLI 进程已关闭")
            logger.info(f"⏱️  总执行时间: {elapsed:.1f}秒")
            logger.info(f"📤 返回码: {process.returncode}")

            # 分析并显示输出
            logger.info("-" * 60)
            logger.info("📊 执行结果分析:")

            # 检查关键输出
            has_messages_checked = False
            messages_sent = False
            tools_used = []

            for line in output_lines:
                line_lower = line.lower()
                if 'check_pending_messages' in line_lower:
                    has_messages_checked = True
                if 'send_telegram_message' in line_lower or 'message sent' in line_lower:
                    messages_sent = True
                if 'mcp__' in line_lower:
                    if 'arxiv' in line_lower:
                        tools_used.append('arXiv搜索')
                    elif '12306' in line_lower:
                        tools_used.append('12306查询')

            logger.info(f"   检查消息: {'是' if has_messages_checked else '否'}")
            logger.info(f"   发送回复: {'是' if messages_sent else '否'}")
            if tools_used:
                logger.info(f"   使用工具: {', '.join(set(tools_used))}")

            # 显示部分输出（前15行）
            if output_lines:
                logger.info("-" * 60)
                logger.info("📝 Claude CLI 输出（前15行）:")
                for i, line in enumerate(output_lines[:15]):
                    if line.strip():
                        logger.info(f"   {line[:100]}")  # 每行最多100字符

            # 显示错误（如果有）
            if error_lines:
                error_count = sum(1 for line in error_lines if line.strip())
                if error_count > 0:
                    logger.warning(f"⚠️ 发现 {error_count} 行错误输出")
                    for line in error_lines[:5]:
                        if line.strip() and 'error' in line.lower():
                            logger.warning(f"   {line[:100]}")

            logger.info("-" * 60)

            if process.returncode == 0:
                logger.info("✅ 任务执行成功")
                return True
            else:
                logger.warning(f"⚠️ 任务执行失败 (返回码: {process.returncode})")
                return False

        except subprocess.TimeoutExpired as e:
            logger.error("❌ 任务执行超时（120秒）")
            logger.info("🔧 正在强制终止超时的 Claude CLI 进程...")

            # 超时时，subprocess.run 会自动终止进程
            # 但我们可以确保清理子进程
            try:
                if e.process:
                    e.process.kill()
                    logger.info("✅ 超时进程已强制终止")
            except Exception as kill_error:
                logger.warning(f"⚠️ 终止进程时出错: {kill_error}")

            return False

        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
            logger.info("🔧 确保进程已清理...")
            return False

        finally:
            # 确保进程资源被释放
            logger.info("🧹 清理完成，准备下一次检查")

    def run(self):
        """主循环"""
        logger.info("=" * 60)
        logger.info("🚀 Claude CLI 调度器启动 - 简单版")
        logger.info("=" * 60)
        logger.info(f"📁 工作目录: {WORKSPACE_DIR}")
        logger.info(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
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
    dispatcher = ClaudeDispatcherSimple()
    dispatcher.run()


if __name__ == "__main__":
    main()


