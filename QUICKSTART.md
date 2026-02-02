# 快速启动指南

## 方法1：使用启动脚本（推荐）

直接双击 `start.bat` 文件，会自动：
1. 激活虚拟环境
2. 启动调度器

## 方法2：手动启动

### Windows

```bash
# 1. 进入项目目录
cd telegram-claude-dispatcher

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 启动调度器
python dispatcher.py
```

### Linux/Mac

```bash
# 1. 进入项目目录
cd telegram-claude-dispatcher

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 启动调度器
python dispatcher.py
```

## 停止调度器

按 `Ctrl+C` 停止运行

## 查看日志

日志文件：`dispatcher.log`

```bash
# 实时查看日志
tail -f dispatcher.log
```
