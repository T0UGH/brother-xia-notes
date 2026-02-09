#!/usr/bin/env python3
"""
Claude Code 更新通知主程序
检查更新并发送飞书通知
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

# 配置
CONFIG_FILE = Path(__file__).parent / ".notification_config.json"
HISTORY_FILE = Path(__file__).parent / "version_history.json"

# 默认的飞书 Webhook（可以通过环境变量或配置文件覆盖）
DEFAULT_WEBHOOK = os.environ.get("FEISHU_WEBHOOK_URL", "")

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_webhook_url():
    """获取 Webhook URL"""
    # 优先级：环境变量 > 配置文件 > 空
    return DEFAULT_WEBHOOK or load_config().get("webhook_url", "")

def run_command(cmd, timeout=30):
    """运行命令"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def get_installed_version():
    """获取安装的版本"""
    returncode, stdout, _ = run_command(["claude", "--version"], timeout=10)
    if returncode == 0:
        import re
        match = re.search(r'(\d+\.\d+\.\d+)', stdout.strip())
        if match:
            return match.group(1)
    return None

def get_npm_version():
    """获取 npm 最新版本"""
    returncode, stdout, _ = run_command(
        ["npm", "view", "@anthropic-ai/claude-code", "version"],
        timeout=10
    )
    if returncode == 0:
        return stdout.strip()
    return None

def send_feishu_notification(title, content, is_error=False):
    """发送飞书通知"""
    webhook_url = get_webhook_url()
    
    if not webhook_url:
        print("❌ 未配置飞书 Webhook")
        return False
    
    # 颜色
    if is_error:
        color = "red"
    elif "更新" in title:
        color = "green"
    else:
        color = "blue"
    
    # 构建卡片消息
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content}
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
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
            print(f"✅ 通知发送成功: {response.read().decode('utf-8')}")
            return True
    except Exception as e:
        print(f"❌ 通知发送失败: {e}")
        return False

def load_history():
    """加载历史"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"versions": [], "last_check": None, "last_notified_version": None}

def save_history(history):
    """保存历史"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def main():
    """主函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查...\n")
    
    # 获取版本
    installed = get_installed_version()
    latest = get_npm_version()
    
    print(f"📦 本地版本: {installed or '无法获取'}")
    print(f"🌐 最新版本: {latest or '无法获取'}\n")
    
    # 加载历史
    history = load_history()
    
    # 检查更新
    has_update = False
    if installed and latest and installed != latest:
        has_update = True
        
        # 检查是否已经通知过这个版本
        if history.get("last_notified_version") == latest:
            print(f"ℹ️ 新版本 {latest} 已通知过，跳过通知")
            has_update = False
    
    # 发送通知
    if has_update:
        print(f"🎉 发现新版本！\n")
        
        # 构建通知内容
        title = f"🎉 Claude Code 有更新！{installed} → {latest}"
        
        content = f"""**新版本发布！**

📦 **当前版本**: `{installed}`
🆕 **最新版本**: `{latest}`

**更新方法**：
```bash
npm install -g @anthropic-ai/claude-code
```

**查看完整更新日志**：
https://github.com/anthropics/claude-code/releases

---
💡 此通知由 Clawdbot 自动发送
"""
        
        # 发送通知
        success = send_feishu_notification(title, content)
        
        if success:
            history["last_notified_version"] = latest
            print("✅ 通知发送成功！")
        else:
            print("❌ 通知发送失败")
    
    # 记录历史
    history["versions"].append({
        "timestamp": datetime.now().isoformat(),
        "installed": installed,
        "latest": latest,
        "has_update": has_update
    })
    
    # 保留最近 50 条
    if len(history["versions"]) > 50:
        history["versions"] = history["versions"][-50:]
    
    history["last_check"] = datetime.now().isoformat()
    save_history(history)
    
    print(f"\n💾 历史记录已保存\n")
    print(f"✅ 检查完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 1 if has_update else 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
