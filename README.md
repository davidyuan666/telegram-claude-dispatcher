# Telegram Claude Dispatcher

一个智能的 Telegram 消息调度器，自动检测新消息并调用 Claude CLI 进行处理和回复。

## ✨ 特性

- 🚀 **智能检测** - 使用独立的 utils 模块快速检查新消息（1-2秒）
- 💡 **按需启动** - 只在有新消息时才启动 Claude CLI，节省资源
- 📊 **详细进度** - 实时显示执行状态、耗时、工具使用情况
- 🔒 **进程管理** - 自动管理进程生命周期，防止重复运行
- 🛡️ **错误处理** - 完善的超时保护和异常处理机制

## 🏗️ 架构

```
调度器 (每30秒)
    ↓
utils 快速检查（1-2秒）
    ↓
有新消息？
    ├─ 否 → 跳过，等待下次
    └─ 是 → 启动 Claude CLI
            ↓
        MCP 工具处理
            ↓
        发送回复
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
# 编辑 .env 文件，填入你的 Telegram Bot Token
```

## 🚀 使用

### 启动调度器

```bash
python dispatcher.py
```

### 配置说明

在 `dispatcher.py` 中可以配置：

- `CHECK_INTERVAL` - 检查间隔（默认30秒）
- `WORKSPACE_DIR` - 工作目录
- `TELEGRAM_ENV_FILE` - Telegram 配置文件路径

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
├── dispatcher.py           # 主调度器
├── utils/
│   ├── __init__.py
│   └── telegram_utils.py   # Telegram 工具模块
├── docs/
│   └── ARCHITECTURE.md     # 架构文档
└── examples/
    └── test_utils.py       # 测试示例
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
