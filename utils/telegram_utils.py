#!/usr/bin/env python3
"""
Telegram 工具模块 - 独立版本（不依赖 MCP）
提供消息接收和发送功能，供调度器和其他 Python 脚本使用
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class TelegramUtils:
    """Telegram 工具类"""

    def __init__(self, bot_token: str = None, state_file: str = None):
        """
        初始化 Telegram 工具

        Args:
            bot_token: Telegram Bot Token，如果不提供则从环境变量读取
            state_file: 状态文件路径，用于保存 last_update_id
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("需要提供 TELEGRAM_BOT_TOKEN")

        # 状态文件路径
        if state_file:
            self.state_file = Path(state_file)
        else:
            self.state_file = Path(__file__).parent / 'telegram_state.json'

        self.last_update_id = self._load_last_update_id()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _load_last_update_id(self) -> int:
        """加载上次处理的 update_id"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return data.get('last_update_id', 0)
        except Exception as e:
            logger.warning(f"加载 last_update_id 失败: {e}")
        return 0

    def _save_last_update_id(self, update_id: int):
        """保存 last_update_id"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({'last_update_id': update_id}, f)
            self.last_update_id = update_id
        except Exception as e:
            logger.error(f"保存 last_update_id 失败: {e}")

    def check_new_messages(self, mark_as_read: bool = False) -> bool:
        """
        快速检查是否有新消息（不获取消息内容）

        Args:
            mark_as_read: 是否标记为已读

        Returns:
            bool: 是否有新消息
        """
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'limit': 1,
                'timeout': 0
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result'):
                    if mark_as_read and data['result']:
                        # 标记为已读
                        latest_update_id = data['result'][-1]['update_id']
                        self._save_last_update_id(latest_update_id)
                    return True
                return False
            else:
                logger.error(f"检查消息失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"检查消息异常: {e}")
            return False

    def get_pending_messages(self, mark_as_read: bool = True) -> List[Dict]:
        """
        获取待处理的消息

        Args:
            mark_as_read: 是否立即标记为已读（默认True，保持向后兼容）

        Returns:
            List[Dict]: 消息列表，每条消息包含：
                - update_id: Update ID（用于后续确认）
                - message_id: 消息ID
                - chat_id: 聊天ID
                - user: 用户信息 (username, first_name)
                - text: 消息文本
                - date: 消息时间
        """
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 0
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.error(f"获取消息失败: {response.status_code}")
                return []

            data = response.json()
            if not data.get('ok'):
                logger.error(f"API 返回错误: {data}")
                return []

            updates = data.get('result', [])
            if not updates:
                return []

            messages = []
            max_update_id = self.last_update_id

            for update in updates:
                update_id = update['update_id']

                # 记录最大的 update_id
                if update_id > max_update_id:
                    max_update_id = update_id

                # 提取消息信息
                if 'message' in update:
                    msg = update['message']
                    messages.append({
                        'update_id': update_id,  # 添加 update_id
                        'message_id': msg.get('message_id'),
                        'chat_id': msg['chat']['id'],
                        'user': {
                            'username': msg['from'].get('username', ''),
                            'first_name': msg['from'].get('first_name', ''),
                        },
                        'text': msg.get('text', ''),
                        'date': msg.get('date')
                    })

            # 如果设置了 mark_as_read，立即更新 last_update_id
            if mark_as_read and max_update_id > self.last_update_id:
                self._save_last_update_id(max_update_id)

            return messages

        except Exception as e:
            logger.error(f"获取消息异常: {e}")
            return []

    def acknowledge_messages(self, update_ids: List[int]) -> bool:
        """
        确认消息已处理，更新 last_update_id

        Args:
            update_ids: 要确认的 update_id 列表

        Returns:
            bool: 是否成功
        """
        try:
            if not update_ids:
                return True

            max_update_id = max(update_ids)
            if max_update_id > self.last_update_id:
                self._save_last_update_id(max_update_id)
                logger.info(f"已确认消息处理完成，更新 last_update_id 到: {max_update_id}")
                return True
            return True

        except Exception as e:
            logger.error(f"确认消息异常: {e}")
            return False

    def send_message(self, chat_id: int, text: str) -> bool:
        """
        发送消息到指定的聊天

        Args:
            chat_id: 聊天ID
            text: 消息文本

        Returns:
            bool: 是否发送成功
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"消息发送成功到 chat_id: {chat_id}")
                    return True
                else:
                    logger.error(f"发送消息失败: {result}")
                    return False
            else:
                logger.error(f"发送消息失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False


# 便捷函数
def create_telegram_utils(env_file: str = None) -> TelegramUtils:
    """
    创建 TelegramUtils 实例，从 .env 文件加载配置

    Args:
        env_file: .env 文件路径

    Returns:
        TelegramUtils 实例
    """
    if env_file and Path(env_file).exists():
        # 从 .env 文件加载环境变量
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    return TelegramUtils()

