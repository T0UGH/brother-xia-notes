#!/usr/bin/env python3
"""
Claude Code 更新通知主程序（带 Release Notes）
- 检查更新
- 获取 GitHub Release Notes
- 发送飞书通知
"""

import json
import subprocess
import sys
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# 文件路径
SCRIPT_DIR = Path(__file__).parent
HISTORY_FILE = SCRIPT_DIR / "version_history.json"
CHANGELOG_FILE = SCRIPT_DIR / "github_changelog.json"

# GitHub 配置
GITHUB_REPO = "anthropics/claude-code"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
CHANGELOG_URL = f"https://github.com/{GITHUB_REPO}/blob/main/CHANGELOG.md"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

def get_env_or_file(key, filepath):
    """从环境变量或文件获取配置"""
    # 环境变量
    value = os.environ.get(key)
    if value:
        return value
    
    # .env 文件
    env_file = filepath.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip().startswith(key + "="):
                    return line.strip().split("=", 1)[1]
    
    return ""

def get_webhook_url():
    """获取飞书 Webhook URL"""
    return get_env_or_file("FEISHU_WEBHOOK_URL", SCRIPT_DIR / ".env")

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
    """获取本地安装的 Claude Code 版本"""
    returncode, stdout, _ = run_command(["claude", "--version"], timeout=10)
    if returncode == 0:
        match = re.search(r'(\d+\.\d+\.\d+)', stdout.strip())
        if match:
            return match.group(1)
    return None

def get_npm_version():
    """从 npm 获取最新版本"""
    returncode, stdout, _ = run_command(
        ["npm", "view", "@anthropic-ai/claude-code", "version"],
        timeout=10
    )
    if returncode == 0:
        return stdout.strip()
    return None

def fetch_github_releases():
    """获取 GitHub Release Notes"""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'ClaudeCode-UpdateChecker'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # 保存到文件
            with open(CHANGELOG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            return data
            
    except Exception as e:
        print(f"⚠️  获取 GitHub releases 失败: {e}")
        return None

def get_release_notes(version):
    """获取特定版本的 release notes"""
    # 首先尝试从 GitHub releases 获取
    releases = fetch_github_releases()
    
    if releases:
        for release in releases:
            if release.get('tag_name', '').lstrip('v') == version:
                return {
                    'version': version,
                    'title': release.get('name', f'v{version}'),
                    'body': release.get('body', ''),
                    'url': release.get('html_url', ''),
                    'published_at': release.get('published_at', '')
                }
    
    # 如果无法获取，返回默认信息
    return {
        'version': version,
        'title': f'v{version}',
        'body': '',
        'url': f'{RELEASES_URL}/tag/v{version}',
        'published_at': ''
    }

def format_release_notes(notes, max_length=2000):
    """格式化 release notes，截断过长内容"""
    body = notes.get('body', '')
    
    if not body:
        return "暂无详细更新说明"
    
    # 清理 markdown 格式，简化内容
    body = re.sub(r'```[\s\S]*?```', '[代码块]', body)  # 代码块
    body = re.sub(r'`([^`]+)`', r'\1', body)  # 行内代码
    body = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', body)  # 链接
    body = re.sub(r'#{1,6}\s*', '', body)  # 标题
    body = re.sub(r'\n{3,}', '\n\n', body)  # 多余空行
    
    # 截断
    if len(body) > max_length:
        body = body[:max_length] + "...\n\n[详细内容请查看 GitHub Release]"
    
    return body.strip()

def send_feishu_notification(title, content, is_update=False):
    """发送飞书通知"""
    webhook_url = get_webhook_url()
    
    if not webhook_url:
        print("❌ 错误：未配置飞书 Webhook URL")
        print("请在 .env 文件中配置 FEISHU_WEBHOOK_URL")
        return False
    
    # 颜色
    if is_update:
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
                        {"tag": "plain_text", "content": f"通知时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                    ]
                }
            ]
        }
    }
    
    # 发送请求
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(card).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            print(f"✅ 飞书通知发送成功")
            return True
            
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

def load_history():
    """加载历史记录"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"versions": [], "last_check": None, "last_notified_version": None}

def save_history(history):
    """保存历史记录"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def main():
    """主函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查 Claude Code 更新...\n")
    
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
            print(f"ℹ️  新版本 {latest} 已通知过，跳过通知")
            has_update = False
    
    # 发送通知
    if has_update:
        print(f"🎉 发现新版本！\n")
        
        # 获取 release notes
        print("📋 正在获取 Release Notes...")
        notes = get_release_notes(latest)
        
        # 格式化 release notes
        release_body = format_release_notes(notes)
        
        # 构建通知内容
        title = f"🎉 Claude Code 有更新！{installed} → {latest}"
        
        content = f"""**Claude Code 新版本发布！**

📦 **当前版本**: `{installed}`
🆕 **最新版本**: `{latest}`
🔗 **Release 页面**: {notes['url']}

---

📝 **更新内容**:

{release_body}

---

💻 **更新方法**：
```bash
npm install -g @anthropic-ai/claude-code
```

📖 **查看完整更新日志**：
https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
"""
        
        # 发送通知
        success = send_feishu_notification(title, content, is_update=True)
        
        if success:
            history["last_notified_version"] = latest
            print("✅ 通知发送成功！")
        else:
            print("❌ 通知发送失败")
    
    # 记录到历史
    history["versions"].append({
        "timestamp": datetime.now().isoformat(),
        "installed": installed,
        "latest": latest,
        "has_update": has_update,
        "release_notes": notes.get('url', '') if has_update else ''
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
