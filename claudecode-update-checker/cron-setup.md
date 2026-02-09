# Claude Code 更新检查器 - Cron 配置

## 安装步骤

### 1. 准备环境

```bash
# 进入项目目录
cd /path/to/claudecode-update-checker

# 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖（如果需要的话）
# pip install requests  # 目前只需要标准库，无需额外依赖

# 给脚本添加执行权限
chmod +x check_update.py
chmod +x run_check.sh
```

### 2. 测试脚本

```bash
# 运行一次检查，查看输出
./run_check.sh
```

输出示例：
```
[2026-02-10 09:30:00] 🎉 发现 Claude Code 更新！
   当前版本: 0.2.35
   最新版本: 0.2.36
```

或者：
```
[2026-02-10 09:30:00] ✅ Claude Code 已是最新版本: 0.2.35
```

### 3. 配置 Cron 任务

#### macOS / Linux

```bash
# 编辑 crontab
crontab -e
```

添加以下行（每天早上 9 点检查一次）：

```cron
# Claude Code 更新检查 - 每天上午 9 点
0 9 * * * /path/to/claudecode-update-checker/run_check.sh >> /path/to/claudecode-update-checker/check.log 2>&1
```

如果需要更频繁的检查（例如每 4 小时）：

```cron
# 每 4 小时检查一次
0 */4 * * * /path/to/claudecode-update-checker/run_check.sh >> /path/to/claudecode-update-checker/check.log 2>&1
```

#### 查看 Cron 任务

```bash
# 列出所有 cron 任务
crontab -l

# 查看日志
tail -f /path/to/claudecode-update-checker/check.log
```

### 4. 添加通知功能（可选）

如果你想在有更新时收到通知（比如飞书、钉钉、邮件等），可以修改 `run_check.sh`：

```bash
# 如果有更新，发送通知
if [ $EXIT_CODE -eq 1 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎉 发现 Claude Code 更新！"
    
    # 发送飞书通知（需要配置 webhook）
    # curl -X POST -H "Content-Type: application/json" \
    #   -d '{"msg_type":"text","content":{"text":"Claude Code 有更新！"}}' \
    #   https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK
    
    # 或者发送邮件
    # echo "Claude Code 有更新！" | mail -s "Claude Code Update" your@email.com
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Claude Code 已是最新版本或检查失败"
fi
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `check_update.py` | 核心检查脚本，查询当前版本和最新版本 |
| `run_check.sh` | 包装脚本，设置环境变量并运行检查 |
| `version_history.json` | 版本历史记录（自动创建） |
| `check.log` | 检查日志（可选） |
| `cron-setup.md` | 本文档 |

---

## 故障排除

### 1. 无法获取版本信息

```bash
# 检查 npm 是否可用
which npm
npm --version

# 检查 claude 命令
which claude
claude --version
```

### 2. 代理问题

如果在中国大陆，确保代理已设置：

```bash
export HTTP_PROXY=http://127.0.0.1:1087
export HTTPS_PROXY=http://127.0.0.1:1087
```

### 3. Cron 任务不执行

检查 cron 日志：

```bash
# macOS
tail -f /var/log/system.log | grep cron

# Linux
tail -f /var/log/cron
```

---

## 高级配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HTTP_PROXY` | HTTP 代理 | http://127.0.0.1:1087 |
| `HTTPS_PROXY` | HTTPS 代理 | http://127.0.0.1:1087 |
| `CLAUDE_UPDATE_CHECK_INTERVAL` | 检查间隔（小时） | 24 |

---

## 总结

1. 编辑 crontab：`crontab -e`
2. 添加任务：`0 9 * * * /path/to/run_check.sh >> /path/to/check.log 2>&1`
3. 查看日志：`tail -f /path/to/check.log`
4. 搞定！🎉
