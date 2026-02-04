# 后台运行脚本使用说明

## 📦 脚本列表

### Linux/Mac 脚本
- `start_daemon.sh` - 启动后台服务
- `stop_daemon.sh` - 停止后台服务
- `restart_daemon.sh` - 重启后台服务
- `status_daemon.sh` - 查看运行状态

### Windows 脚本
- `start_daemon.bat` - 启动后台服务
- `stop_daemon.bat` - 停止后台服务

## 🚀 使用方法

### Linux/Mac

#### 1. 赋予执行权限
```bash
chmod +x start_daemon.sh stop_daemon.sh restart_daemon.sh status_daemon.sh
```

#### 2. 启动服务
```bash
./start_daemon.sh
```

输出示例：
```
==========================================
🚀 启动 Telegram-Claude Dispatcher
==========================================
📦 启动 Dispatcher（后台模式）...
✅ Dispatcher 启动成功！
   PID: 12345
   日志: dispatcher.log

查看日志: tail -f dispatcher.log
停止服务: ./stop_daemon.sh
查看状态: ./status_daemon.sh
==========================================
```

#### 3. 查看状态
```bash
./status_daemon.sh
```

输出示例：
```
==========================================
📊 Telegram-Claude Dispatcher 状态
==========================================
状态: ✅ 运行中
PID: 12345
运行时间: 01:23:45
内存使用: 45 MB
日志文件: dispatcher.log (2.3M)

最近日志（最后10行）:
----------------------------------------
[日志内容...]
==========================================
```

#### 4. 停止服务
```bash
./stop_daemon.sh
```

#### 5. 重启服务
```bash
./restart_daemon.sh
```

#### 6. 查看实时日志
```bash
tail -f dispatcher.log
```

---

### Windows

#### 1. 启动服务
双击运行 `start_daemon.bat` 或在命令行中：
```cmd
start_daemon.bat
```

#### 2. 停止服务
双击运行 `stop_daemon.bat` 或在命令行中：
```cmd
stop_daemon.bat
```

#### 3. 查看日志
```cmd
type dispatcher.log
```

或使用文本编辑器打开 `dispatcher.log`

---

## 🔧 高级用法

### 开机自启动（Linux）

#### 方法1：使用 systemd

创建服务文件 `/etc/systemd/system/telegram-dispatcher.service`：
```ini
[Unit]
Description=Telegram-Claude Dispatcher
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/telegram-claude-dispatcher
ExecStart=/usr/bin/python3 /path/to/telegram-claude-dispatcher/dispatcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable telegram-dispatcher
sudo systemctl start telegram-dispatcher
sudo systemctl status telegram-dispatcher
```

#### 方法2：使用 crontab
```bash
crontab -e
```

添加：
```
@reboot cd /path/to/telegram-claude-dispatcher && ./start_daemon.sh
```

### 开机自启动（Windows）

将 `start_daemon.bat` 的快捷方式放到启动文件夹：
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## 📝 注意事项

1. **日志管理**：日志文件会持续增长，建议定期清理
2. **权限问题**：确保脚本有执行权限（Linux/Mac）
3. **环境变量**：确保 `.env` 文件配置正确
4. **进程监控**：建议配合 `status_daemon.sh` 定期检查状态

---

**版本**: 3.2.0
**更新日期**: 2026-02-04
**新增功能**: 后台运行脚本




