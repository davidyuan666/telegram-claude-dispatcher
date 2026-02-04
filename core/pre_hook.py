#!/usr/bin/env python3
"""
PreHook 处理器模块
负责在消息发送给 Claude CLI 之前进行预处理
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PreHook:
    """PreHook 处理器 - 消息接收预处理"""

    def __init__(self, config: Dict = None):
        """
        初始化 PreHook 处理器

        Args:
            config: 配置字典，包含白名单、黑名单、限流等配置
        """
        self.config = config or {}

        # 白名单用户（如果设置，只有这些用户可以使用）
        self.whitelist = set(self.config.get('whitelist', []))

        # 黑名单用户
        self.blacklist = set(self.config.get('blacklist', []))

        # 限流配置（每个用户每分钟最多请求数）
        self.rate_limit = self.config.get('rate_limit', 10)
        self.rate_limit_window = {}  # {user_id: [timestamp1, timestamp2, ...]}

        # 命令路由配置
        self.command_handlers = {
            '/help': self._handle_help,
            '/status': self._handle_status,
            '/ping': self._handle_ping,
        }

        logger.info("✅ PreHook 初始化完成")
        if self.whitelist:
            logger.info(f"   - 白名单模式: {len(self.whitelist)} 个用户")
        if self.blacklist:
            logger.info(f"   - 黑名单: {len(self.blacklist)} 个用户")
        logger.info(f"   - 限流: {self.rate_limit} 请求/分钟")

    def process(self, messages: List[Dict]) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        处理接收到的消息

        Args:
            messages: 消息列表

        Returns:
            Tuple[bool, Optional[str], List[Dict]]:
                - bool: 是否继续处理（True=继续，False=拦截）
                - Optional[str]: 如果拦截，返回给用户的消息
                - List[Dict]: 处理后的消息列表（可能被修改或增强）
        """
        try:
            logger.info("🔍 PreHook: 开始处理消息...")

            for msg in messages:
                user_id = msg.get('user', {}).get('id')
                username = msg.get('user', {}).get('username', 'unknown')
                text = msg.get('text', '')

                logger.info(f"   - 用户: {username} (ID: {user_id})")
                logger.info(f"   - 内容: {text[:50]}...")

                # 1. 权限检查
                check_result, error_msg = self._check_permissions(user_id, username)
                if not check_result:
                    logger.warning(f"❌ 权限检查失败: {error_msg}")
                    return False, error_msg, messages

                # 2. 限流检查
                check_result, error_msg = self._check_rate_limit(user_id)
                if not check_result:
                    logger.warning(f"❌ 限流检查失败: {error_msg}")
                    return False, error_msg, messages

                # 3. 命令路由
                if text.startswith('/'):
                    command = text.split()[0].lower()
                    if command in self.command_handlers:
                        logger.info(f"🎯 命令路由: {command}")
                        response = self.command_handlers[command](msg)
                        return False, response, messages

                # 4. 消息增强（添加上下文）
                msg['_prehook_metadata'] = {
                    'processed_at': datetime.now().isoformat(),
                    'user_id': user_id,
                    'username': username,
                }

            logger.info("✅ PreHook: 消息检查通过，继续处理")
            return True, None, messages

        except Exception as e:
            logger.error(f"❌ PreHook 处理失败: {e}")
            return False, f"系统错误: {str(e)}", messages

    def _check_permissions(self, user_id: int, username: str) -> Tuple[bool, Optional[str]]:
        """
        检查用户权限

        Returns:
            Tuple[bool, Optional[str]]: (是否通过, 错误消息)
        """
        # 黑名单检查
        if user_id in self.blacklist or username in self.blacklist:
            return False, "❌ 您已被禁止使用此服务"

        # 白名单检查（如果启用）
        if self.whitelist:
            if user_id not in self.whitelist and username not in self.whitelist:
                return False, "❌ 抱歉，您没有权限使用此服务"

        return True, None

    def _check_rate_limit(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        检查限流

        Returns:
            Tuple[bool, Optional[str]]: (是否通过, 错误消息)
        """
        now = datetime.now()

        # 初始化用户记录
        if user_id not in self.rate_limit_window:
            self.rate_limit_window[user_id] = []

        # 清理过期记录（超过1分钟）
        self.rate_limit_window[user_id] = [
            ts for ts in self.rate_limit_window[user_id]
            if (now - ts).total_seconds() < 60
        ]

        # 检查是否超过限流
        if len(self.rate_limit_window[user_id]) >= self.rate_limit:
            return False, f"⚠️ 请求过于频繁，请稍后再试（限制: {self.rate_limit} 次/分钟）"

        # 记录本次请求
        self.rate_limit_window[user_id].append(now)

        return True, None

    def _handle_help(self, msg: Dict) -> str:
        """处理 /help 命令"""
        return """📖 帮助信息

可用命令：
/help - 显示此帮助信息
/status - 查看系统状态
/ping - 测试连接

其他消息将由 AI 助手处理。

支持的功能：
- 🔍 搜索学术论文（arXiv）
- 🚄 查询火车票（12306）
- 📄 文档处理
- 💬 智能对话

有问题请直接发送消息！"""

    def _handle_status(self, msg: Dict) -> str:
        """处理 /status 命令"""
        return f"""✅ 系统状态

🤖 服务状态: 运行中
⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👥 活跃用户: {len(self.rate_limit_window)}

一切正常！"""

    def _handle_ping(self, msg: Dict) -> str:
        """处理 /ping 命令"""
        return "🏓 Pong! 系统运行正常。"

