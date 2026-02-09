# Claude Code 更新检查器

自动检查 Claude Code CLI 更新，并通过飞书通知你。

## 🚀 快速开始（3步搞定）

### 第 1 步：获取飞书 Webhook（2分钟）

1. 打开飞书 → 进入任意群聊（或创建新群）
2. 群设置 → 群机器人 → 添加机器人
3. 选择「**自定义机器人**」
4. **复制 Webhook 地址**（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx`）

### 第 2 步：配置（1分钟）

```bash
cd ~/brother-xia-notes/claudecode-update-checker

# 编辑配置文件
vim .env
```

修改这一行：
```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
```

### 第 3 步：启动！（1分钟）

```bash
# 配置定时任务（每天自动检查）
./setup-cron.sh

# 立即测试一次
python3 notify_update.py
```

完成！✅ 系统会每天自动检查，有新版本就发飞书通知你。

---

## 📱 你会收到的通知

当 Claude Code 有更新时，飞书会收到：

```
🎉 Claude Code 有更新！0.2.35 → 0.2.36

📦 当前版本: 0.2.35
🆕 最新版本: 0.2.36

**更新方法**：
npm install -g @anthropic-ai/claude-code

**查看完整更新日志**：
https://github.com/anthropics/claude-code/releases
```

---

## 🛠️ 常用命令

### 手动检查更新
```bash
python3 notify_update.py
```

### 查看版本历史
```bash
cat version_history.json | jq
```

### 查看检查日志
```bash
tail -f check.log
```

### 修改检查时间
```bash
crontab -e
# 修改这行（例如改成每天下午3点）：
0 15 * * * cd ~/brother-xia-notes/claudecode-update-checker && python3 notify_update.py >> check.log 2>&1
```

---

## 📂 文件说明

```
claudecode-update-checker/
├── README.md                    # 📖 本文档
├── .env                         # 🔐 配置文件（需要配置 Webhook）
├── .env.example                 # 📝 配置模板
├── notify_update.py             # 🔔 主程序：检查+通知
├── send_feishu_notification.py  # 📱 飞书通知工具
├── setup-cron.sh                # ⏰ 配置定时任务
├── check_update.py              # 🔍 基础检查
├── version_history.json         # 📊 版本历史
└── check.log                    # 📝 运行日志（自动生成）
```

---

## ❓ 常见问题

**Q: 没有收到飞书通知？**
- 检查 `.env` 文件中的 `FEISHU_WEBHOOK_URL` 是否正确
- 检查飞书机器人是否有权限发送消息
- 运行 `python3 notify_update.py` 测试

**Q: 如何临时禁用自动检查？**
```bash
crontab -e
# 注释掉这一行（前面加 #）：
# 0 9 * * * cd ~/brother-xia-notes/claudecode-update-checker && python3 notify_update.py >> check.log 2>&1
```

**Q: 如何更改检查时间？**
```bash
crontab -e
# 修改时间（格式：分 时 * * *）
# 例如改成每天下午3点：
0 15 * * * cd ~/brother-xia-notes/claudecode-update-checker && python3 notify_update.py >> check.log 2>&1
```

---

有问题随时找我！🚀
