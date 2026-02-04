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

    def check_new_messages(self, mark_as_read: bool = False, max_retries: int = 2, long_polling: bool = True) -> bool:
        """
        快速检查是否有新消息（支持长轮询，减少请求频率）

        Args:
            mark_as_read: 是否标记为已读
            max_retries: 最大重试次数（默认2次）
            long_polling: 是否使用长轮询（默认True）
                         True: Telegram服务器等待25秒再返回，大幅减少请求
                         False: 立即返回

        Returns:
            bool: 是否有新消息
        """
        import time

        # 长轮询配置：让服务器等待最多25秒
        # 这样可以从"每10秒请求一次"变为"有消息才返回"
        polling_timeout = 25 if long_polling else 0
        request_timeout = 30 if long_polling else 8

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/getUpdates"
                params = {
                    'offset': self.last_update_id + 1,
                    'limit': 1,
                    'timeout': polling_timeout
                }

                response = requests.get(url, params=params, timeout=request_timeout)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok') and data.get('result'):
                        if mark_as_read and data['result']:
                            latest_update_id = data['result'][-1]['update_id']
                            self._save_last_update_id(latest_update_id)
                        return True
                    return False
                else:
                    logger.error(f"检查消息失败: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return False

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"网络错误，重试中...")
                    time.sleep(1)
                else:
                    logger.error(f"检查消息网络异常: {e}")
                    return False
            except Exception as e:
                logger.error(f"检查消息异常: {e}")
                return False

        return False

    def get_pending_messages(self, mark_as_read: bool = True, max_retries: int = 3) -> List[Dict]:
        """
        获取待处理的消息（带重试机制）

        Args:
            mark_as_read: 是否立即标记为已读（默认True，保持向后兼容）
            max_retries: 最大重试次数（默认3次）

        Returns:
            List[Dict]: 消息列表，每条消息包含：
                - update_id: Update ID（用于后续确认）
                - message_id: 消息ID
                - chat_id: 聊天ID
                - user: 用户信息 (username, first_name)
                - text: 消息文本
                - date: 消息时间
        """
        import time

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/getUpdates"
                params = {
                    'offset': self.last_update_id + 1,
                    'timeout': 0
                }

                response = requests.get(url, params=params, timeout=15)

                if response.status_code != 200:
                    logger.error(f"获取消息失败: {response.status_code}")
                    if attempt < max_retries - 1:
                        logger.info(f"🔄 重试 {attempt + 1}/{max_retries}...")
                        time.sleep(2)
                        continue
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
                            'update_id': update_id,
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

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    ConnectionResetError) as e:
                logger.warning(f"网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避：2, 4, 8秒
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 达到最大重试次数，放弃获取消息")
                    return []

            except Exception as e:
                logger.error(f"获取消息异常: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 重试 {attempt + 1}/{max_retries}...")
                    time.sleep(2)
                else:
                    return []

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

    def send_message(self, chat_id: int, text: str, max_retries: int = 3) -> bool:
        """
        发送消息到指定的聊天（带重试机制）

        Args:
            chat_id: 聊天ID
            text: 消息文本
            max_retries: 最大重试次数（默认3次）

        Returns:
            bool: 是否发送成功
        """
        import time

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': text
                }

                response = requests.post(url, json=data, timeout=15)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.info(f"消息发送成功到 chat_id: {chat_id}")
                        return True
                    else:
                        logger.error(f"发送消息失败: {result}")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        return False
                else:
                    logger.error(f"发送消息失败: HTTP {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                logger.warning(f"发送消息网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 达到最大重试次数，发送失败")
                    return False

            except Exception as e:
                logger.error(f"发送消息异常: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return False

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

