#!/bin/bash
# Claude Code 更新检查器 - 一键配置脚本（简化版）

echo "🤖 Claude Code 更新检查器 - 一键配置"
echo "======================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 第1步：配置飞书 Webhook
echo "📱 第1步：配置飞书通知"
echo "------------------------"
echo ""
echo "请按以下步骤获取飞书 Webhook："
echo "1. 打开飞书 → 进入任意群聊"
echo "2. 群设置 → 群机器人 → 添加机器人"
echo "3. 选择「自定义机器人」→ 复制 Webhook 地址"
echo ""

read -p "请输入飞书 Webhook URL: " WEBHOOK_URL

if [[ ! $WEBHOOK_URL == https* ]]; then
    echo "❌ URL 格式不正确"
    exit 1
fi

# 保存配置
cat > .env << EOF
# Claude Code 更新检查器配置
FEISHU_WEBHOOK_URL=$WEBHOOK_URL
HTTP_PROXY=http://127.0.0.1:1087
HTTPS_PROXY=http://127.0.0.1:1087
EOF

echo "✅ 配置已保存"
echo ""

# 第2步：测试通知
echo "🧪 第2步：测试通知"
echo "-------------------"
echo ""

export FEISHU_WEBHOOK_URL="$WEBHOOK_URL"
export HTTP_PROXY=http://127.0.0.1:1087
export HTTPS_PROXY=http://127.0.0.1:1087

python3 << 'PYEOF'
import json
import urllib.request
import sys

webhook = "$FEISHU_WEBHOOK_URL"

card = {
    "msg_type": "interactive",
    "card": {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "🎉 Claude Code 更新检查器配置成功！"},
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**Claude Code 更新检查器已成功配置！**\n\n📋 功能:\n• 每天自动检查 Claude Code 新版本\n• 发现更新时发送飞书通知\n• 包含版本号和更新命令\n\n🕐 检查时间: 每天上午 9:00"
                }
            }
        ]
    }
}

try:
    req = urllib.request.Request(
        webhook,
        data=json.dumps(card).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        response.read().decode('utf-8')
    print("✅ 测试通知发送成功！请检查飞书是否收到消息。")
    sys.exit(0)
except Exception as e:
    print(f"❌ 发送失败: {e}")
    print("请检查 Webhook URL 是否正确。")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️ 通知测试失败，但配置已保存。"
    echo "可以稍后手动运行测试：python3 notify_update.py"
fi

echo ""

# 第3步：配置定时任务
echo "⏰ 第3步：配置定时检查"
echo "-----------------------"
echo ""

read -p "是否配置每天自动检查？ (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 创建临时文件
    TEMP_CRON=$(mktemp)
    
    # 获取现有 crontab
    crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# 新建 crontab" > "$TEMP_CRON"
    
    # 检查是否已存在
    if grep -q "claudecode-update-checker" "$TEMP_CRON"; then
        echo "⚠️ 已存在定时任务，是否更新？"
        read -p "(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            grep -v "claudecode-update-checker" "$TEMP_CRON" > "${TEMP_CRON}.tmp"
            mv "${TEMP_CRON}.tmp" "$TEMP_CRON"
        else
            echo "保持现有配置"
            rm -f "$TEMP_CRON"
            exit 0
        fi
    fi
    
    # 添加新任务（每天早上 9 点）
    echo "" >> "$TEMP_CRON"
    echo "# Claude Code 更新检查 - 每天上午 9 点" >> "$TEMP_CRON"
    echo "0 9 * * * cd $SCRIPT_DIR && python3 notify_update.py >> check.log 2>&1 # claudecode-update-checker" >> "$TEMP_CRON"
    
    # 安装新 crontab
    crontab "$TEMP_CRON"
    rm -f "$TEMP_CRON"
    
    echo "✅ 定时任务已配置！"
    echo ""
    echo "任务详情："
    echo "  执行时间: 每天上午 9:00"
    echo "  执行命令: python3 notify_update.py"
    echo "  日志文件: $SCRIPT_DIR/check.log"
else
    echo ""
    echo "⚠️ 跳过了定时配置"
    echo ""
    echo "稍后可以通过以下命令手动配置："
    echo "  crontab -e"
    echo ""
    echo "添加以下内容（每天早上9点检查）："
    echo "  0 9 * * * cd $SCRIPT_DIR && python3 notify_update.py >> check.log 2>&1"
fi

echo ""
echo "======================================"
echo "🎉 配置完成！"
echo "======================================"
echo ""
echo "现在你可以："
echo ""
echo "1. 立即测试检查："
echo "   python3 notify_update.py"
echo ""
echo "2. 查看配置："
echo "   cat .env"
echo ""
echo "3. 查看日志："
echo "   tail -f check.log"
echo ""
echo "4. 查看定时任务："
echo "   crontab -l"
echo ""
echo "💡 提示：如果飞书通知没有收到，检查："
echo "  1. .env 文件中的 FEISHU_WEBHOOK_URL 是否正确"
echo "  2. 飞书机器人是否有权限发送消息"
echo "  3. 网络连接是否正常"
echo ""
echo "有问题随时找我！🚀"
