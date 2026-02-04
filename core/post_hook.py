#!/usr/bin/env python3
"""
PostHook 处理器模块
负责在消息发送到 Telegram 之前进行后处理
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PostHook:
    """PostHook 处理器 - 消息发送后处理"""

    def __init__(self, config: Dict = None):
        """
        初始化 PostHook 处理器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 最大消息长度（Telegram 限制 4096 字符）
        self.max_length = self.config.get('max_length', 4000)

        # 是否启用消息美化
        self.enable_formatting = self.config.get('enable_formatting', True)

        # 是否添加时间戳
        self.add_timestamp = self.config.get('add_timestamp', False)

        logger.info("✅ PostHook 初始化完成")
        logger.info(f"   - 最大长度: {self.max_length} 字符")
        logger.info(f"   - 消息美化: {'启用' if self.enable_formatting else '禁用'}")
        logger.info(f"   - 时间戳: {'启用' if self.add_timestamp else '禁用'}")

    def process(self, output: str, messages: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        处理 Claude CLI 输出，提取并格式化回复内容

        Args:
            output: Claude CLI 的原始输出
            messages: 原始消息列表（用于上下文）

        Returns:
            Tuple[bool, Optional[str], Optional[str]]:
                - bool: 是否成功提取回复
                - Optional[str]: 提取的回复内容
                - Optional[str]: 错误消息（如果失败）
        """
        try:
            logger.info("🔍 PostHook: 开始处理输出...")
            logger.info(f"   - 原始输出长度: {len(output)} 字符")

            # 1. 提取回复内容
            reply_content = self._extract_reply_content(output)

            if not reply_content:
                logger.warning("⚠️ 未能提取回复内容")
                return False, None, "未能生成回复内容"

            logger.info(f"   - 提取到回复: {len(reply_content)} 字符")

            # 2. 清理和格式化
            reply_content = self._clean_content(reply_content)

            # 3. 消息美化
            if self.enable_formatting:
                reply_content = self._format_content(reply_content)

            # 4. 长度检查和分割
            if len(reply_content) > self.max_length:
                logger.warning(f"⚠️ 消息过长 ({len(reply_content)} 字符)，将截断")
                reply_content = self._truncate_content(reply_content)

            # 5. 添加时间戳（可选）
            if self.add_timestamp:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                reply_content = f"{reply_content}\n\n⏰ {timestamp}"

            logger.info(f"✅ PostHook: 处理完成，最终长度: {len(reply_content)} 字符")
            return True, reply_content, None

        except Exception as e:
            logger.error(f"❌ PostHook 处理失败: {e}")
            return False, None, f"处理输出失败: {str(e)}"

    def _extract_reply_content(self, output: str) -> Optional[str]:
        """
        从输出中提取回复内容

        优先级：
        1. 查找 ===REPLY_START=== 标记
        2. 智能提取（过滤系统输出）
        """
        # 方法1: 标记模式
        pattern = r'===REPLY_START===(.*?)===REPLY_END==='
        match = re.search(pattern, output, re.DOTALL)

        if match:
            logger.info("   ✓ 使用标记模式提取")
            return match.group(1).strip()

        # 方法2: 智能提取
        logger.info("   ✓ 使用智能提取模式")
        return self._smart_extract(output)

    def _smart_extract(self, output: str) -> Optional[str]:
        """智能提取回复内容（过滤系统输出）"""
        lines = output.split('\n')
        content_lines = []

        # 需要跳过的模式
        skip_patterns = [
            r'^完成[！!]',
            r'^## 处理总结',
            r'^\*\*收到的消息',
            r'^\*\*处理结果',
            r'^✅.*已.*',
            r'^- 用户[:：]',
            r'^- 内容[:：]',
            r'^- \d+个',
        ]

        in_summary = False
        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # 检测总结部分
            if '## 处理总结' in line_stripped or '**收到的消息' in line_stripped:
                in_summary = True
                continue

            if in_summary:
                continue

            # 跳过匹配的模式
            should_skip = any(re.match(pattern, line_stripped) for pattern in skip_patterns)

            if not should_skip:
                content_lines.append(line_stripped)

        return '\n'.join(content_lines) if content_lines else None

    def _clean_content(self, content: str) -> str:
        """清理内容（移除多余空行、特殊字符等）"""
        # 移除多余的空行
        lines = [line.rstrip() for line in content.split('\n')]

        # 合并连续的空行
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if not line:
                if not prev_empty:
                    cleaned_lines.append(line)
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        return '\n'.join(cleaned_lines).strip()

    def _format_content(self, content: str) -> str:
        """美化内容格式"""
        # 这里可以添加更多格式化逻辑
        # 例如：添加 Markdown 格式、emoji 等
        return content

    def _truncate_content(self, content: str) -> str:
        """截断过长的内容"""
        if len(content) <= self.max_length:
            return content

        # 截断并添加提示
        truncated = content[:self.max_length - 50]

        # 尝试在句子边界截断
        last_period = truncated.rfind('。')
        last_newline = truncated.rfind('\n')
        cut_point = max(last_period, last_newline)

        if cut_point > self.max_length * 0.8:  # 至少保留80%
            truncated = truncated[:cut_point + 1]

        return truncated + "\n\n⚠️ (内容过长，已截断)"


