#!/bin/bash
# Claude Code 更新检查器 - 设置向导

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🤖 Claude Code 更新检查器 - 设置向导"
echo "======================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3，请先安装 Python3"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误：未找到 npm，请先安装 Node.js"
    exit 1
fi

echo "✅ npm 已安装: $(npm --version)"

# 检查 claude 命令
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null | head -1 || echo "unknown")
    echo "✅ Claude Code 已安装: $CLAUDE_VERSION"
else
    echo "⚠️ 警告：未找到 Claude Code 命令，可能无法获取本地版本"
fi

echo ""

# 配置飞书 Webhook
echo "📱 飞书通知配置"
echo "----------------"
echo ""
echo "要发送飞书通知，需要配置飞书机器人的 Webhook URL。"
echo ""
echo "获取方法："
echo "1. 打开飞书，进入一个群聊"
echo "2. 点击群设置 → 群机器人"
echo "3. 添加机器人 → 自定义机器人"
echo "4. 复制 Webhook 地址"
echo ""

read -p "是否现在配置飞书 Webhook？ (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "请输入飞书 Webhook URL: " WEBHOOK_URL
    
    if [[ $WEBHOOK_URL == https* ]]; then
        # 保存配置
        python3 << EOF
import json
with open('.feishu_config.json', 'w') as f:
    json.dump({'webhook_url': '$WEBHOOK_URL'}, f)
print("✅ 配置已保存")
EOF
        
        echo ""
        echo "🧪 正在发送测试通知..."
        
        # 发送测试通知
        python3 notify_update.py << 'TEST_EOF'
test
TEST_EOF
        
        echo ""
        echo "如果收到了飞书消息，说明配置成功！"
    else
        echo "❌ URL 格式不正确，应以 https:// 开头"
    fi
else
    echo ""
    echo "⚠️ 跳过飞书配置，稍后可以通过以下命令配置："
    echo "  python3 send_feishu_notification.py --setup"
fi

echo ""
echo "📝 Cron 任务配置"
echo "----------------"
echo ""
echo "要每天自动检查更新，需要配置 cron 任务。"
echo ""

read -p "是否现在配置 cron 任务？ (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 获取当前脚本的绝对路径
    CHECK_SCRIPT="$SCRIPT_DIR/notify_update.py"
    
    # 创建临时文件
    TEMP_CRON=$(mktemp)
    
    # 获取现有 crontab
    crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# 新建 crontab" > "$TEMP_CRON"
    
    # 检查是否已存在
    if grep -q "claudecode-update-checker" "$TEMP_CRON"; then
        echo "⚠️ 已存在 Claude Code 更新检查的 cron 任务，跳过添加"
    else
        # 添加新任务（每天早上 9 点）
        echo "" >> "$TEMP_CRON"
        echo "# Claude Code 更新检查 - 每天上午 9 点" >> "$TEMP_CRON"
        echo "0 9 * * * cd $SCRIPT_DIR && python3 notify_update.py >> check.log 2>&1" >> "$TEMP_CRON"
        
        # 安装新 crontab
        crontab "$TEMP_CRON"
        
        echo "✅ Cron 任务已添加！"
        echo ""
        echo "任务详情："
        echo "  执行时间: 每天上午 9:00"
        echo "  执行命令: python3 notify_update.py"
        echo "  日志文件: $SCRIPT_DIR/check.log"
    fi
    
    # 清理临时文件
    rm -f "$TEMP_CRON"
    
    echo ""
    echo "查看 cron 任务："
    echo "  crontab -l"
    echo ""
    echo "查看日志："
    echo "  tail -f $SCRIPT_DIR/check.log"
else
    echo ""
    echo "⚠️ 跳过 cron 配置"
    echo ""
    echo "稍后可以通过以下命令手动配置："
    echo "  crontab -e"
    echo ""
    echo "添加以下内容（每天早上9点检查）："
    echo "  0 9 * * * cd $SCRIPT_DIR && python3 notify_update.py >> check.log 2>&1"
fi

echo ""
echo "======================================"
echo "🎉 设置完成！"
echo "======================================"
echo ""
echo "现在你可以："
echo ""
echo "1. 立即测试检查："
echo "   cd $SCRIPT_DIR && python3 notify_update.py"
echo ""
echo "2. 查看版本历史："
echo "   cat $SCRIPT_DIR/version_history.json"
echo ""
echo "3. 手动发送测试通知（配置了飞书的情况下）："
echo "   python3 send_feishu_notification.py --setup"
echo ""
echo "有问题随时找我！🚀"
