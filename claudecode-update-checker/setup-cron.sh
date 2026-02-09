#!/bin/bash
# Claude Code 更新检查器 - 定时任务配置脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "⏰ Claude Code 更新检查器 - 定时任务配置"
echo "=========================================="
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ 错误：未找到 .env 配置文件"
    echo "请先复制 .env.example 到 .env 并配置 FEISHU_WEBHOOK_URL"
    echo ""
    echo "步骤："
    echo "  cp .env.example .env"
    echo "  vim .env  # 编辑配置"
    exit 1
fi

# 检查 Webhook URL 是否配置
if ! grep -q "FEISHU_WEBHOOK_URL=https" .env; then
    echo "⚠️ 警告：FEISHU_WEBHOOK_URL 未配置"
    echo ""
    echo "请先编辑 .env 文件，配置飞书 Webhook URL："
    echo "  vim .env"
    echo ""
    echo "将 FEISHU_WEBHOOK_URL= 改为："
    echo "  FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
    exit 1
fi

echo "✅ 配置检查通过"
echo ""

# 检查现有 crontab
echo "📋 检查现有定时任务..."
echo ""

TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# 新建 crontab" > "$TEMP_CRON"

if grep -q "claudecode-update-checker" "$TEMP_CRON"; then
    echo "⚠️ 已存在 Claude Code 更新检查的定时任务"
    echo ""
    echo "当前任务："
    grep "claudecode-update-checker" "$TEMP_CRON" | sed 's/^/  /'
    echo ""
    
    read -p "是否重新配置？ (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 删除旧任务
        grep -v "claudecode-update-checker" "$TEMP_CRON" > "${TEMP_CRON}.tmp"
        mv "${TEMP_CRON}.tmp" "$TEMP_CRON"
        echo "✅ 已删除旧配置"
        echo ""
    else
        echo "保持现有配置"
        rm -f "$TEMP_CRON"
        exit 0
    fi
fi

# 配置新任务
echo "🕐 配置定时任务"
echo "---------------"
echo ""
echo "选择检查时间："
echo "  1) 每天早上 9:00（推荐）"
echo "  2) 每天早上 8:00"
echo "  3) 每天晚上 20:00"
echo "  4) 自定义"
echo ""

read -p "请输入选项 (1-4): " -n 1 -r
echo

case $REPLY in
    1)
        HOUR=9
        MINUTE=0
        ;;
    2)
        HOUR=8
        MINUTE=0
        ;;
    3)
        HOUR=20
        MINUTE=0
        ;;
    4)
        read -p "请输入小时 (0-23): " HOUR
        read -p "请输入分钟 (0-59): " MINUTE
        ;;
    *)
        echo "无效选项，使用默认时间 9:00"
        HOUR=9
        MINUTE=0
        ;;
esac

echo ""
echo "✅ 定时任务设置：每天 ${HOUR}:${MINUTE}"
echo ""

# 添加新任务
echo "" >> "$TEMP_CRON"
echo "# Claude Code 更新检查 - 每天 ${HOUR}:${MINUTE}" >> "$TEMP_CRON"
echo "${MINUTE} ${HOUR} * * * cd $SCRIPT_DIR && python3 notify_update.py >> check.log 2>&1 # claudecode-update-checker" >> "$TEMP_CRON"

# 安装新 crontab
crontab "$TEMP_CRON"
rm -f "$TEMP_CRON"

echo "✅ 定时任务已配置！"
echo ""
echo "任务详情："
echo "  执行时间: 每天 ${HOUR}:${MINUTE}"
echo "  执行命令: python3 notify_update.py"
echo "  日志文件: $SCRIPT_DIR/check.log"
echo ""

# 建议立即测试
echo "🧪 建议立即测试一次："
echo ""
echo "  python3 notify_update.py"
echo ""

# 显示帮助信息
echo "📚 常用命令："
echo ""
echo "  查看日志:          tail -f check.log"
echo "  查看历史:          cat version_history.json | jq"
echo "  手动检查:          python3 notify_update.py"
echo "  查看定时任务:      crontab -l"
echo "  修改定时时间:      crontab -e"
echo ""
echo "======================================"
echo "🎉 配置完成！"
echo "======================================"
echo ""
