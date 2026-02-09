#!/usr/bin/env python3
"""
Feishu 通知发送器
当 Claude Code 有更新时发送飞书通知
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

# Feishu Webhook 配置
# 请在这里填入你的飞书机器人 webhook URL
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")

# 或者从配置文件读取
CONFIG_FILE = Path(__file__).parent / ".feishu_config.json"

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("webhook_url", "")
        except:
            pass
    return ""

def save_config(webhook_url):
    """保存配置"""
    config = {"webhook_url": webhook_url}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_webhook_url():
    """获取 webhook URL"""
    # 优先级：环境变量 > 配置文件 > 空
    return FEISHU_WEBHOOK_URL or load_config() or ""

def send_feishu_notification(title, content, is_error=False):
    """发送飞书通知
    
    Args:
        title: 通知标题
        content: 通知内容（支持 markdown）
        is_error: 是否是错误通知
    """
    webhook_url = get_webhook_url()
    
    if not webhook_url:
        print("❌ 错误：未配置飞书 Webhook URL", file=sys.stderr)
        print("请设置以下之一：", file=sys.stderr)
        print("  1. 环境变量：export FEISHU_WEBHOOK_URL='https://open.feishu.cn/...'", file=sys.stderr)
        print("  2. 运行：python3 send_feishu_notification.py --setup", file=sys.stderr)
        return False
    
    # 根据类型设置颜色
    if is_error:
        header_color = "red"
        header_title = "❌ 错误通知"
    elif "更新" in title:
        header_color = "green"
        header_title = "🎉 更新提醒"
    else:
        header_color = "blue"
        header_title = "📢 系统通知"
    
    # 构建消息卡片
    card_message = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": header_title
                },
                "template": header_color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{title}**"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"通知时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }
    
    # 发送请求
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(card_message).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            print(f"✅ 飞书通知发送成功: {result}")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误: {e.code} - {e.reason}", file=sys.stderr)
        print(f"响应: {e.read().decode('utf-8')}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ 发送失败: {e}", file=sys.stderr)
        return False

def setup_webhook():
    """交互式配置 webhook"""
    print("🤖 Claude Code 更新检查器 - 飞书通知配置")
    print("=" * 50)
    print()
    print("请按以下步骤获取飞书 Webhook URL：")
    print()
    print("1. 打开飞书，进入一个群聊")
    print("2. 点击群设置 → 群机器人")
    print("3. 添加机器人 → 自定义机器人")
    print("4. 复制 Webhook 地址")
    print()
    
    webhook_url = input("请输入你的飞书 Webhook URL: ").strip()
    
    if not webhook_url.startswith("https://"):
        print("❌ URL 格式不正确，应以 https:// 开头")
        return False
    
    # 保存配置
    save_config(webhook_url)
    print(f"✅ 配置已保存到: {CONFIG_FILE}")
    
    # 测试发送
    print("\n🧪 正在发送测试通知...")
    success = send_feishu_notification(
        "测试通知",
        "如果你看到这条消息，说明 Claude Code 更新检查器的飞书通知配置成功！\n\n今后当 Claude Code 有新版本时，你会在这里收到通知。",
        is_error=False
    )
    
    if success:
        print("✅ 测试通知发送成功！")
    else:
        print("❌ 测试通知发送失败，请检查 Webhook URL 是否正确")
    
    return success

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="发送 Claude Code 更新通知到飞书")
    parser.add_argument("--setup", action="store_true", help="配置飞书 Webhook")
    parser.add_argument("--title", help="通知标题")
    parser.add_argument("--content", help="通知内容")
    parser.add_argument("--error", action="store_true", help="标记为错误通知")
    
    args = parser.parse_args()
    
    if args.setup:
        success = setup_webhook()
        sys.exit(0 if success else 1)
    
    if args.title and args.content:
        # 直接发送通知模式
        success = send_feishu_notification(args.title, args.content, args.error)
        sys.exit(0 if success else 1)
    
    # 默认：显示帮助
    parser.print_help()
    print("\n示例:")
    print("  python3 send_feishu_notification.py --setup")
    print("  python3 send_feishu_notification.py --title '测试' --content '这是一条测试消息'")

if __name__ == "__main__":
    main()
