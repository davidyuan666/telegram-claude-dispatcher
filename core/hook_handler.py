#!/usr/bin/env python3
"""
Hook处理器模块
负责捕获和解析Claude CLI的输出，提取关键信息
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HookHandler:
    """Hook处理器 - 解析Claude CLI输出"""

    def __init__(self):
        """初始化Hook处理器"""
        self.tool_patterns = {
            'telegram_send': r'(mcp__telegram-sender__|send.*telegram|发送.*telegram|telegram.*消息)',
            'telegram_file': r'(mcp__telegram-file-sender__|send.*document|发送.*文件)',
            'arxiv': r'(mcp__arxiv-search__|arxiv|论文|paper)',
            '12306': r'(mcp__12306-mcp__|12306|火车票|车票)',
            'medical': r'(mcp__medical-search__|medical|医学)',
        }

    def parse_output(self, output: str) -> Dict:
        """
        解析Claude CLI输出

        Args:
            output: Claude CLI的标准输出

        Returns:
            Dict: 解析结果，包含工具使用情况、消息发送状态等
        """
        result = {
            'tools_used': [],
            'messages_sent': False,
            'files_sent': False,
            'task_complete': False,
            'errors': []
        }

        try:
            lines = output.split('\n')

            for line in lines:
                line_lower = line.lower()

                # 检查任务完成标记
                if 'task_complete' in line_lower:
                    result['task_complete'] = True

                # 检查工具使用
                for tool_name, pattern in self.tool_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        if tool_name not in result['tools_used']:
                            result['tools_used'].append(tool_name)

                        # 特殊标记
                        if tool_name == 'telegram_send':
                            result['messages_sent'] = True
                        elif tool_name == 'telegram_file':
                            result['files_sent'] = True

                # 检查错误
                if 'error' in line_lower and 'error' not in line_lower.startswith('#'):
                    result['errors'].append(line.strip())

            logger.info(f"输出解析完成: {len(result['tools_used'])} 个工具被使用")

        except Exception as e:
            logger.error(f"解析输出失败: {e}")
            result['errors'].append(f"解析失败: {str(e)}")

        return result

    def extract_reply_content(self, output: str) -> Optional[str]:
        """
        从输出中提取回复内容

        Args:
            output: Claude CLI输出

        Returns:
            Optional[str]: 提取的回复内容，如果没有找到则返回None
        """
        try:
            import re

            # 方法1: 匹配 ===REPLY_START=== 和 ===REPLY_END=== 之间的内容
            pattern = r'===REPLY_START===(.*?)===REPLY_END==='
            match = re.search(pattern, output, re.DOTALL)

            if match:
                reply = match.group(1).strip()
                logger.info(f"✅ 提取到回复内容（标记模式），长度: {len(reply)} 字符")
                return reply

            # 方法2: 如果没有找到标记，尝试智能提取
            # 在 --print 模式下，Claude CLI 会直接输出最终回复
            logger.warning("未找到回复内容标记，尝试智能提取...")

            # 移除常见的系统输出模式
            lines = output.split('\n')
            content_lines = []
            skip_patterns = [
                r'^完成[！!]',
                r'^## 处理总结',
                r'^\*\*收到的消息',
                r'^\*\*处理结果',
                r'^✅',
                r'^- 用户[:：]',
                r'^- 内容[:：]',
                r'^- \d+个',
                r'^- 票价',
                r'^- 出发',
            ]

            in_summary = False
            for line in lines:
                line_stripped = line.strip()

                # 跳过空行
                if not line_stripped:
                    continue

                # 检测是否进入总结部分
                if '## 处理总结' in line_stripped or '**收到的消息' in line_stripped:
                    in_summary = True
                    continue

                # 如果在总结部分，跳过
                if in_summary:
                    continue

                # 跳过匹配的模式
                should_skip = False
                for pattern in skip_patterns:
                    if re.match(pattern, line_stripped):
                        should_skip = True
                        break

                if not should_skip and line_stripped:
                    content_lines.append(line_stripped)

            if content_lines:
                reply = '\n'.join(content_lines)
                logger.info(f"✅ 智能提取到回复内容，长度: {len(reply)} 字符")
                return reply

            logger.warning("⚠️ 无法提取回复内容")
            return None

        except Exception as e:
            logger.error(f"提取回复内容失败: {e}")
            return None

    def extract_chat_ids(self, output: str) -> List[int]:
        """
        从输出中提取chat_id

        Args:
            output: Claude CLI输出

        Returns:
            List[int]: chat_id列表
        """
        chat_ids = []
        try:
            # 匹配 chat_id 模式
            pattern = r'chat_id["\s:=]+(\d+)'
            matches = re.findall(pattern, output, re.IGNORECASE)

            for match in matches:
                chat_id = int(match)
                if chat_id not in chat_ids:
                    chat_ids.append(chat_id)

            logger.info(f"提取到 {len(chat_ids)} 个chat_id")

        except Exception as e:
            logger.error(f"提取chat_id失败: {e}")

        return chat_ids

    def format_summary(self, parse_result: Dict) -> str:
        """
        格式化解析结果为摘要

        Args:
            parse_result: 解析结果

        Returns:
            str: 格式化的摘要
        """
        summary_lines = []

        if parse_result['task_complete']:
            summary_lines.append("✅ 任务完成")
        else:
            summary_lines.append("⚠️ 任务未完成")

        if parse_result['tools_used']:
            tools = ', '.join(parse_result['tools_used'])
            summary_lines.append(f"🔧 使用工具: {tools}")

        if parse_result['messages_sent']:
            summary_lines.append("📤 消息已发送")

        if parse_result['files_sent']:
            summary_lines.append("📎 文件已发送")

        if parse_result['errors']:
            summary_lines.append(f"❌ 发现 {len(parse_result['errors'])} 个错误")

        return '\n'.join(summary_lines)
