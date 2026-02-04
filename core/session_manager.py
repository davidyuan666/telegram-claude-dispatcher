#!/usr/bin/env python3
"""
会话管理器模块
负责管理 Claude CLI 会话的生命周期，确保任务隔离和资源清理
"""
import os
import uuid
import logging
import shutil
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """会话管理器 - 管理 Claude CLI 会话的隔离和生命周期"""

    def __init__(self, base_sessions_dir: Path):
        """
        初始化会话管理器

        Args:
            base_sessions_dir: 会话存储的基础目录
        """
        self.base_sessions_dir = Path(base_sessions_dir)
        self.base_sessions_dir.mkdir(parents=True, exist_ok=True)
        self.active_sessions: Dict[str, Dict] = {}
        logger.info(f"会话管理器初始化完成，会话目录: {self.base_sessions_dir}")

    def create_session(self, message_id: str = None) -> Dict:
        """
        创建新的隔离会话

        Args:
            message_id: 消息ID（可选，用于追踪）

        Returns:
            Dict: 会话信息，包含 session_id, session_dir, created_at 等
        """
        try:
            # 生成唯一的会话ID
            session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

            # 创建会话专用目录
            session_dir = self.base_sessions_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            # 记录会话信息
            session_info = {
                'session_id': session_id,
                'session_dir': session_dir,
                'message_id': message_id,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }

            self.active_sessions[session_id] = session_info
            logger.info(f"✅ 创建新会话: {session_id}")

            return session_info

        except Exception as e:
            logger.error(f"❌ 创建会话失败: {e}")
            raise

    def cleanup_session(self, session_id: str, keep_logs: bool = False) -> bool:
        """
        清理会话资源

        Args:
            session_id: 会话ID
            keep_logs: 是否保留日志文件

        Returns:
            bool: 清理是否成功
        """
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"⚠️ 会话不存在: {session_id}")
                return False

            session_info = self.active_sessions[session_id]
            session_dir = session_info['session_dir']

            # 如果需要保留日志，先备份
            if keep_logs and session_dir.exists():
                log_files = list(session_dir.glob("*.log"))
                if log_files:
                    logs_backup_dir = self.base_sessions_dir / "logs_archive"
                    logs_backup_dir.mkdir(exist_ok=True)
                    for log_file in log_files:
                        backup_path = logs_backup_dir / f"{session_id}_{log_file.name}"
                        shutil.copy2(log_file, backup_path)
                    logger.info(f"📦 已备份 {len(log_files)} 个日志文件")

            # 删除会话目录
            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.info(f"🗑️  已删除会话目录: {session_dir}")

            # 从活动会话中移除
            session_info['status'] = 'cleaned'
            del self.active_sessions[session_id]

            logger.info(f"✅ 会话清理完成: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 清理会话失败 ({session_id}): {e}")
            return False

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        清理超过指定时间的旧会话

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            int: 清理的会话数量
        """
        try:
            from datetime import timedelta

            cleaned_count = 0
            current_time = datetime.now()
            sessions_to_clean = []

            # 找出需要清理的会话
            for session_id, session_info in self.active_sessions.items():
                created_at = datetime.fromisoformat(session_info['created_at'])
                age = current_time - created_at

                if age > timedelta(hours=max_age_hours):
                    sessions_to_clean.append(session_id)

            # 清理旧会话
            for session_id in sessions_to_clean:
                if self.cleanup_session(session_id, keep_logs=True):
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"🧹 已清理 {cleaned_count} 个超过 {max_age_hours} 小时的旧会话")

            return cleaned_count

        except Exception as e:
            logger.error(f"❌ 清理旧会话失败: {e}")
            return 0

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict]: 会话信息，如果不存在则返回 None
        """
        return self.active_sessions.get(session_id)

    def list_active_sessions(self) -> list:
        """
        列出所有活动会话

        Returns:
            list: 活动会话列表
        """
        return list(self.active_sessions.values())

    def get_stats(self) -> Dict:
        """
        获取会话统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            'active_sessions': len(self.active_sessions),
            'sessions_dir': str(self.base_sessions_dir),
            'sessions': [
                {
                    'session_id': info['session_id'],
                    'message_id': info.get('message_id'),
                    'created_at': info['created_at'],
                    'status': info['status']
                }
                for info in self.active_sessions.values()
            ]
        }
