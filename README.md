# Telegram Claude Dispatcher - 重构版

一个智能的 Telegram 消息调度器，仿照 OpenCrawl 架构设计，自动检测新消息并调用无头 Claude CLI 进行处理和回复。

## ✨ 特性

- 🚀 **智能检测** - 使用独立的 utils 模块快速检查新消息（1-2秒）
- 💡 **按需启动** - 只在有新消息时才启动 Claude CLI，节省资源
- 🏗️ **模块化架构** - 仿照 OpenCrawl，清晰的模块划分
- 📊 **详细进度** - 实时显示执行状态、耗时、工具使用情况
- 🔒 **Sandbox 模式** - 默认启用 sandbox 模式，确保安全隔离
- 📦 **会话隔离** - 每个请求使用独立会话，避免任务间干扰
- 🗑️ **自动清理** - 任务完成后自动清理会话资源
- 🛡️ **错误处理** - 完善的超时保护和异常处理机制
- 🔄 **自动重试** - 失败的消息会在下次检查时重新处理
- ⚙️ **可配置** - 通过环境变量灵活配置

## 🏗️ 架构（仿照 OpenCrawl）

```
Telegram Bot
    ↓
Dispatcher (定时检查)
    ↓
Utils 快速检查（1-2秒）
    ↓
有新消息？
    ├─ 否 → 跳过，等待下次
    └─ 是 → SessionManager (创建独立会话)
            ↓
        MessageProcessor
            ↓
        无头 Claude CLI (Sandbox 模式)
            ↓
        独立会话目录 (.claude_sessions/session_xxx/)
            ↓
        MCP 工具处理
            ↓
        HookHandler 解析结果
            ↓
        返回 Telegram
            ↓
        SessionManager (清理会话)
```

## 📦 安装

### 前置要求

- Python 3.8+
- Claude CLI (已安装并配置)
- Telegram Bot Token

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/telegram-claude-dispatcher.git
cd telegram-claude-dispatcher
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入以下配置：
# TELEGRAM_BOT_TOKEN=你的bot token
# TELEGRAM_CHAT_ID=你的chat id
# CLAUDE_CLI_PATH=Claude CLI路径（可选）
# POLLING_INTERVAL=轮询间隔秒数（可选，默认10）
```

## 🚀 使用

### 启动调度器

```bash
python dispatcher.py
```

### 配置说明

在 `.env` 文件中配置：

- `TELEGRAM_BOT_TOKEN` - Telegram Bot Token（必需）
- `TELEGRAM_CHAT_ID` - 默认聊天ID（必需）
- `CLAUDE_CLI_PATH` - Claude CLI路径（可选，默认为 'claude'）
- `ENABLE_SANDBOX` - 是否启用 sandbox 模式（可选，默认为 'true'，强烈推荐）
- `POLLING_INTERVAL` - 检查间隔秒数（可选，默认10秒）

**重要安全说明：**
- 默认启用 `ENABLE_SANDBOX=true`，确保每个任务在隔离环境中运行
- 每个请求使用独立的会话目录，避免任务间相互干扰
- 会话完成后自动清理资源，保留日志用于调试

### 核心模块

- **dispatcher.py** - 主调度器，协调各组件工作
- **core/message_processor.py** - 消息处理器，调用无头Claude CLI（支持sandbox和会话隔离）
- **core/session_manager.py** - 会话管理器，管理独立会话的生命周期
- **core/hook_handler.py** - Hook处理器，解析Claude输出
- **utils/telegram_utils.py** - Telegram工具，快速检查和发送消息

## 📊 运行示例

```
🚀 Claude CLI 调度器启动 - 简单版
📁 工作目录: /path/to/workspace
⏰ 检查间隔: 30秒
✅ 已获取进程锁 (PID: 12345)

🔄 第 1 次检查 (总运行: 0.0分钟)
📥 快速检查是否有新的 Telegram 消息...
   检查耗时: 1.52秒
✅ 没有新消息
💤 跳过本次处理，节省资源

😴 休眠 30 秒...
```

当有新消息时：

```
📬 发现新消息！
📤 启动 Claude CLI 处理消息...
🚀 正在启动 Claude CLI...
✅ Claude CLI 已启动 (PID: 23456)
📊 开始监控执行进度...
⏳ 执行中... 已用时 10秒
⏳ 执行中... 已用时 20秒
🔒 Claude CLI 进程已关闭
⏱️  总执行时间: 25.3秒
📤 返回码: 0

📊 执行结果分析:
   检查消息: 是
   发送回复: 是
   使用工具: arXiv搜索

✅ 任务执行成功
```

## 🛠️ 开发

### 项目结构

```
telegram-claude-dispatcher/
├── dispatcher.py           # 主调度器（重构版）
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── message_processor.py   # 消息处理器（支持sandbox和会话隔离）
│   ├── session_manager.py     # 会话管理器
│   └── hook_handler.py        # Hook处理器
├── utils/                  # 工具模块
│   ├── __init__.py
│   └── telegram_utils.py   # Telegram工具
├── docs/
│   └── ARCHITECTURE.md     # 架构文档
├── .env                    # 环境配置
├── .claude_sessions/       # 会话目录（自动创建和清理）
└── dispatcher.log          # 运行日志
```

### 测试

```bash
python examples/test_utils.py
```

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题，请提交 Issue。
