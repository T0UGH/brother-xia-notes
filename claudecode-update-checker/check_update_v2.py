#!/usr/bin/env python3
"""
Claude Code 更新检查器 v2
- 检查版本更新
- 获取更新日志 (changelog)
- 发送通知
"""

import json
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "version_history.json"
NOTIFICATION_FILE = Path(__file__).parent / ".notification_pending"

def run_command(cmd, timeout=30):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def get_installed_version():
    """获取当前安装的 Claude Code 版本"""
    returncode, stdout, stderr = run_command(["claude", "--version"], timeout=10)
    if returncode == 0:
        # 输出可能是 "claude 0.2.35" 或 "0.2.35"
        match = re.search(r'(\d+\.\d+\.\d+)', stdout.strip())
        if match:
            return match.group(1)
    return None

def get_npm_version():
    """从 npm 获取最新版本"""
    returncode, stdout, stderr = run_command(
        ["npm", "view", "@anthropic-ai/claude-code", "version"],
        timeout=10
    )
    if returncode == 0:
        return stdout.strip()
    return None

def get_npm_changelog(version):
    """尝试获取 changelog 信息"""
    # npm view 可以获取更多信息
    returncode, stdout, stderr = run_command(
        ["npm", "view", "@anthropic-ai/claude-code", "--json"],
        timeout=15
    )
    
    changelog_info = []
    
    if returncode == 0:
        try:
            data = json.loads(stdout)
            # 尝试获取各种信息
            if "description" in data:
                changelog_info.append(f"📋 描述: {data['description']}")
            if "homepage" in data:
                changelog_info.append(f"🔗 主页: {data['homepage']}")
            if "repository" in data and isinstance(data['repository'], dict):
                url = data['repository'].get('url', '')
                if url:
                    changelog_info.append(f"📦 仓库: {url}")
        except:
            pass
    
    # GitHub releases 页面通常是查看 changelog 的最佳地方
    changelog_info.append("\n📋 查看完整更新日志:")
    changelog_info.append("   https://github.com/anthropics/claude-code/releases")
    
    return "\n".join(changelog_info)

def load_history():
    """加载版本历史"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"versions": [], "last_check": None, "last_notified_version": None}

def save_history(history):
    """保存版本历史"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def write_notification(installed, latest, changelog):
    """写入待发送的通知"""
    notification = {
        "timestamp": datetime.now().isoformat(),
        "installed_version": installed,
        "latest_version": latest,
        "changelog": changelog,
        "title": f"🎉 Claude Code 有更新！{installed} → {latest}"
    }
    with open(NOTIFICATION_FILE, 'w') as f:
        json.dump(notification, f, indent=2)
    print(f"📧 通知已写入: {NOTIFICATION_FILE}")

def main():
    """主函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检查 Claude Code 更新...\n")
    
    # 获取版本
    installed = get_installed_version()
    latest = get_npm_version()
    
    print(f"📦 已安装版本: {installed or '无法获取'}")
    print(f"🌐 最新版本: {latest or '无法获取'}")
    print()
    
    # 加载历史
    history = load_history()
    
    # 检查是否有更新
    has_update = False
    changelog = ""
    
    if installed and latest:
        if installed != latest:
            has_update = True
            print("🎉 发现新版本！")
            
            # 获取 changelog
            print("📋 正在获取更新信息...")
            changelog = get_npm_changelog(latest)
            
            # 显示 changelog
            print("\n" + "="*60)
            print(changelog)
            print("="*60 + "\n")
            
            # 写入通知文件（供 Clawdbot 读取并发送通知）
            write_notification(installed, latest, changelog)
            
        else:
            print("✅ 已是最新版本，无需更新。\n")
    else:
        print("⚠️ 无法获取版本信息，请检查网络连接。\n")
    
    # 记录到历史
    history["versions"].append({
        "timestamp": datetime.now().isoformat(),
        "installed": installed,
        "latest": latest,
        "has_update": has_update
    })
    
    # 只保留最近 50 条记录
    if len(history["versions"]) > 50:
        history["versions"] = history["versions"][-50:]
    
    history["last_check"] = datetime.now().isoformat()
    
    if has_update:
        history["last_notified_version"] = latest
    
    save_history(history)
    
    print(f"💾 历史记录已保存到: {HISTORY_FILE}\n")
    
    return 1 if has_update else 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
