#!/usr/bin/env python3
"""
消息处理器模块
负责接收Telegram消息，调用无头Claude CLI处理，并返回结果
支持 sandbox 模式和会话隔离
"""
import os
import sys
import json
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class MessageProcessor:
    """消息处理器 - 处理Telegram消息并调用Claude CLI（支持sandbox和会话隔离）"""

    def __init__(self, workspace_dir: str, claude_cli_path: str = None):
        """
        初始化消息处理器

        Args:
            workspace_dir: 工作目录
            claude_cli_path: Claude CLI路径（可选）
        """
        self.workspace_dir = Path(workspace_dir)
        self.claude_cli_path = claude_cli_path or 'claude'

        # 初始化会话管理器
        sessions_dir = self.workspace_dir / '.claude_sessions'
        self.session_manager = SessionManager(sessions_dir)

        logger.info(f"消息处理器初始化完成")
        logger.info(f"  - 工作目录: {self.workspace_dir}")
        logger.info(f"  - 无头模式: 启用（跳过权限检查）")
        logger.info(f"  - 会话目录: {sessions_dir}")

    def format_message_for_claude(self, messages: List[Dict]) -> str:
        """
        格式化消息为Claude CLI的输入提示词

        Args:
            messages: 消息列表

        Returns:
            str: 格式化后的提示词
        """
        messages_info = "\n".join([
            f"消息 {i}:\n"
            f"  - Chat ID: {msg['chat_id']}\n"
            f"  - 用户: {msg['user']['username']} ({msg['user']['first_name']})\n"
            f"  - 内容: {msg['text']}\n"
            for i, msg in enumerate(messages, 1)
        ])

        prompt = f"""你收到了 {len(messages)} 条新的 Telegram 消息，需要处理并生成回复内容。

【消息详情】
{messages_info}

【重要说明】
- 你只需要生成回复内容，不需要发送消息
- Dispatcher 会自动将你的回复发送到 Telegram
- 使用合适的 MCP 工具处理请求（如搜索论文、查询车票等）

【关键要求 - 必须遵守】
你必须按照以下格式输出，这是强制性的：

1. 首先处理用户请求（使用 MCP 工具等）
2. 然后在输出的最后，必须包含以下格式的回复内容：

===REPLY_START===
[这里写给用户的完整回复内容，包括查询结果、建议等]
===REPLY_END===

注意：
- ===REPLY_START=== 和 ===REPLY_END=== 标记是必需的
- 标记之间的内容会被直接发送给 Telegram 用户
- 不要在标记外写给用户的内容，只在标记内写
"""
        return prompt

    def process_messages(self, messages: List[Dict], timeout: int = 180) -> Dict:
        """
        处理消息 - 调用无头Claude CLI（使用独立会话）

        Args:
            messages: 消息列表
            timeout: 超时时间（秒）

        Returns:
            Dict: 处理结果，包含 success, output, error, session_id 等字段
        """
        session_id = None
        try:
            logger.info(f"开始处理 {len(messages)} 条消息")

            # 创建独立会话
            message_id = messages[0].get('message_id', 'unknown') if messages else 'unknown'
            session_info = self.session_manager.create_session(message_id=str(message_id))
            session_id = session_info['session_id']
            session_dir = session_info['session_dir']

            logger.info(f"📦 已创建独立会话: {session_id}")

            # 格式化提示词
            prompt = self.format_message_for_claude(messages)

            # 调用Claude CLI（无头模式，使用独立会话目录）
            result = self._call_claude_cli(prompt, timeout, session_dir)
            result['session_id'] = session_id

            return result

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'session_id': session_id
            }
        finally:
            # 清理会话（保留日志以便调试）
            if session_id:
                self.session_manager.cleanup_session(session_id, keep_logs=True)

    def _call_claude_cli(self, prompt: str, timeout: int, session_dir: Path) -> Dict:
        """
        调用Claude CLI（无头模式，支持 sandbox 和会话隔离）

        Args:
            prompt: 提示词
            timeout: 超时时间
            session_dir: 会话专用目录

        Returns:
            Dict: 执行结果
        """
        try:
            logger.info("启动Claude CLI（无头模式 + Sandbox）...")

            # 构建命令（非交互式模式）
            cmd = [
                self.claude_cli_path,
                '--print',  # 非交互式输出
                '--dangerously-skip-permissions'  # 跳过权限检查
            ]
            logger.info("🤖 非交互式模式：--print + --dangerously-skip-permissions")

            # 添加提示词
            cmd.append(prompt)

            # 设置环境变量（会话隔离）
            env = os.environ.copy()
            env['CLAUDE_SESSION_DIR'] = str(session_dir)

            logger.info(f"📁 会话工作目录: {session_dir}")

            # 调试信息
            logger.info(f"🔍 调试: sys.platform={sys.platform}")
            logger.info(f"🔍 调试: claude_cli_path={self.claude_cli_path}")
            logger.info(f"🔍 调试: 是否.cmd={self.claude_cli_path.endswith('.cmd')}")

            # Windows 上 .cmd 文件需要特殊处理
            if sys.platform == 'win32' and self.claude_cli_path.endswith('.cmd'):
                # Windows .cmd 文件需要 shell=True，并且命令需要转为字符串
                cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in cmd])
                logger.info(f"🪟 Windows 模式，使用 shell=True")
                logger.info(f"📝 命令: {cmd_str[:100]}...")

                process = subprocess.Popen(
                    cmd_str,
                    cwd=self.workspace_dir,  # 使用工作空间目录而不是会话目录
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    shell=True
                )
            else:
                # 其他平台使用列表形式，更安全
                process = subprocess.Popen(
                    cmd,
                    cwd=self.workspace_dir,  # 使用工作空间目录
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    shell=False
                )

            logger.info(f"✅ Claude CLI已启动 (PID: {process.pid})")

            # 实时监控执行进度
            import time
            import threading

            start_time = time.time()
            is_running = True

            def monitor_progress():
                """监控执行进度"""
                while is_running:
                    elapsed = int(time.time() - start_time)
                    if elapsed > 0 and elapsed % 10 == 0:  # 每10秒报告一次
                        logger.info(f"⏳ 执行中... 已用时 {elapsed} 秒")
                    time.sleep(1)

            # 启动监控线程
            monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
            monitor_thread.start()

            # 等待完成
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode
                is_running = False  # 停止监控

                elapsed = time.time() - start_time
                logger.info(f"✅ Claude CLI执行完成 (返回码: {returncode}, 耗时: {elapsed:.1f}秒)")

                # 显示输出统计
                logger.info(f"📊 输出统计: stdout={len(stdout)} 字符, stderr={len(stderr)} 字符")

                return {
                    'success': returncode == 0,
                    'output': stdout,
                    'error': stderr,
                    'returncode': returncode
                }

            except subprocess.TimeoutExpired:
                is_running = False  # 停止监控
                logger.error(f"❌ Claude CLI执行超时（{timeout}秒）")
                process.kill()
                stdout, stderr = process.communicate()
                return {
                    'success': False,
                    'output': stdout,
                    'error': f"执行超时（{timeout}秒）\n{stderr}",
                    'returncode': -1
                }

        except Exception as e:
            logger.error(f"❌ 调用Claude CLI失败: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
