#!/bin/bash
# Claude Code 更新检查器 - 配置向导

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🤖 Claude Code 更新检查器 - 配置向导"
echo "======================================"
echo ""

# 检查依赖
echo "📋 检查依赖..."

if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3，请先安装 Python3"
    exit 1
fi

echo "  ✅ Python3: $(python3 --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ 错误：未找到 npm，请先安装 Node.js"
    exit 1
fi

echo "  ✅ npm: $(npm --version)"

# 检查 claude 命令
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null | head -1 || echo "unknown")
    echo "  ✅ Claude Code: $CLAUDE_VERSION"
else
    echo "  ⚠️  Claude Code 命令未找到，可能无法获取本地版本"
fi

echo ""

# 配置飞书 Webhook
echo "📱 飞书通知配置"
echo "----------------"
echo ""
echo "要发送飞书通知，需要配置飞书机器人的 Webhook URL。"
echo ""
echo "获取方法："
echo "1. 打开飞书，进入一个群聊（或创建一个新的群）"
echo "2. 点击群设置 → 群机器人"
echo "3. 添加机器人 → 自定义机器人"
echo "4. 设置机器人名称和头像，然后复制 Webhook 地址"
echo ""

# 检查是否已有配置
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

if [ -n "$FEISHU_WEBHOOK_URL" ]; then
    echo "✅ 检测到已有配置: ${FEISHU_WEBHOOK_URL:0:50}..."
    read -p "是否重新配置? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "保持现有配置"
        WEBHOOK_URL="$FEISHU_WEBHOOK_URL"
    fi
fi

if [ -z "$WEBHOOK_URL" ]; then
    read -p "请输入飞书 Webhook URL: " WEBHOOK_URL
fi

if [[ $WEBHOOK_URL == https* ]]; then
    # 保存到 .env 文件
    cat > "$ENV_FILE" << EOF
# Claude Code 更新检查器配置
# 生成时间: $(date)

# 飞书 Webhook URL
FEISHU_WEBHOOK_URL=$WEBHOOK_URL

# 代理设置
HTTP_PROXY=http://127.0.0.1:1087
HTTPS_PROXY=http://127.0.0.1:1087

# 检查时间 (24小时制)
CHECK_HOUR=9
CHECK_MINUTE=0
EOF

    echo "✅ 配置已保存到: $ENV_FILE"
    
    # 测试通知
    echo ""
    echo "🧪 正在发送测试通知到飞书..."
    
    export FEISHU_WEBHOOK_URL="$WEBHOOK_URL"
    export HTTP_PROXY=http://127.0.0.1:1087
    export HTTPS_PROXY=http://127.0.0.1:1087
    
    python3 << 'PYEOF'
import json
import urllib.request
import sys

webhook_url = "WEBHOOK_URL_PLACEHOLDER"

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
                    "content": "**Claude Code 更新检查器已成功配置！**\n\n📋 功能说明:\n• 每天自动检查 Claude Code 新版本\n• 发现更新时发送飞书通知\n• 包含版本号和更新日志链接\n\n🕐 检查时间: 每天上午 9:00"
                }
            },
            {
                "tag": "note",
                "elements": [
                    {"tag": "plain_text", "content": "配置完成时间: 刚刚"}
                ]
            }
        ]
    }
}

try:
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(card).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = response.read().decode('utf-8')
        print(f"✅ 测试通知发送成功!")
        sys.exit(0)
except Exception as e:
    print(f"❌ 发送失败: {e}")
    sys.exit(1)
PYEOF
    WEBHOOK_URL="$WEBHOOK_URL" python3 -c "
import json, urllib.request, sys
webhook = '$WEBHOOK_URL'
card = {
    'msg_type': 'interactive',
    'card': {
        'config': {'wide_screen_mode': True},
        'header': {
            'title': {'tag': 'plain_text', 'content': '🎉 Claude Code 更新检查器配置成功！'},
            'template': 'green'
        },
        'elements': [
            {
                'tag': 'div',
                'text': {
                    'tag': 'lark_md',
                    'content': '**Claude Code 更新检查器已成功配置！**\n\n📋 功能说明:\n• 每天自动检查 Claude Code 新版本\n• 发现更新时发送飞书通知\n• 包含版本号和更新日志链接\n\n🕐 检查时间: 每天上午 9:00'
                }
            }
        ]
    }
}
try:
    req = urllib.request.Request(webhook, data=json.dumps(card).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(req, timeout=30)
    print('✅ 测试通知发送成功!')
except Exception as e:
    print(f'❌ 发送失败: {e}')
"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 配置完成！请检查飞书是否收到了测试通知。"
    else
        echo ""
        echo "⚠️ 测试通知发送失败，但配置已保存。"
        echo "请检查 Webhook URL 是否正确。"
    fi
else
    echo "❌ 配置无效，请重试"
    exit 1
fi

echo ""

# 配置 Cron
echo "🕐 Cron 任务配置"
echo "----------------"
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
        echo "⚠️ 已存在 Claude Code 更新检查的 cron 任务"
        read -p "是否更新？ (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 删除旧任务
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
    
    echo "✅ Cron 任务已配置！"
    echo ""
    echo "任务详情："
    echo "  执行时间: 每天上午 9:00"
    echo "  执行命令: python3 notify_update.py"
    echo "  日志文件: $SCRIPT_DIR/check.log"
    echo ""
    echo "查看所有 cron 任务："
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
echo "项目文件："
echo "  $SCRIPT_DIR"
echo ""
echo "核心文件："
echo "  notify_update.py       - 检查更新并发送通知"
echo "  send_feishu_notification.py - 飞书通知工具"
echo "  check_update.py        - 基础检查脚本"
echo "  .env                   - 配置文件（已生成）"
echo "  setup.sh               - 此设置向导"
echo ""
echo "日志文件："
echo "  check.log              - 运行日志"
echo "  version_history.json   - 版本历史"
echo ""
echo "使用说明："
echo "  1. 手动检查更新：python3 notify_update.py"
echo "  2. 查看日志：tail -f check.log"
echo "  3. 查看历史：cat version_history.json | jq"
echo "  4. 重新配置：./setup.sh"
echo ""
echo "💡 提示：如果飞书通知没有收到，检查："
echo "  1. .env 文件中的 FEISHU_WEBHOOK_URL 是否正确"
echo "  2. 飞书机器人是否有权限发送消息"
echo "  3. 网络连接是否正常"
echo ""
echo "有问题随时找我！🚀"
