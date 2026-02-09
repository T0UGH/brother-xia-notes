#!/usr/bin/env python3
"""
Claude Code 更新检查器
每天检查 Claude Code CLI 是否有新版本
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 历史版本记录文件
HISTORY_FILE = Path(__file__).parent / "version_history.json"

def get_current_version():
    """获取当前安装的 Claude Code 版本"""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"获取当前版本失败: {e}", file=sys.stderr)
    return None

def get_latest_version_from_npm():
    """从 npm 获取最新版本"""
    try:
        result = subprocess.run(
            ["npm", "view", "@anthropic-ai/claude-code", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"获取 npm 版本失败: {e}", file=sys.stderr)
    return None

def load_version_history():
    """加载版本历史"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"versions": [], "last_check": None}

def save_version_history(history):
    """保存版本历史"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def main():
    """主函数"""
    print(f"[{datetime.now().isoformat()}] 检查 Claude Code 更新...")
    
    # 获取当前版本和最新版本
    current_version = get_current_version()
    latest_version = get_latest_version_from_npm()
    
    # 加载历史记录
    history = load_version_history()
    
    # 检查是否有更新
    has_update = False
    if current_version and latest_version:
        if current_version != latest_version:
            has_update = True
            print(f"🎉 发现新版本!")
            print(f"   当前版本: {current_version}")
            print(f"   最新版本: {latest_version}")
        else:
            print(f"✅ 已是最新版本: {current_version}")
    else:
        print(f"⚠️ 无法获取版本信息")
        if latest_version:
            print(f"   最新版本: {latest_version}")
    
    # 记录到历史
    history["versions"].append({
        "timestamp": datetime.now().isoformat(),
        "current": current_version,
        "latest": latest_version,
        "has_update": has_update
    })
    history["last_check"] = datetime.now().isoformat()
    
    # 只保留最近 30 条记录
    if len(history["versions"]) > 30:
        history["versions"] = history["versions"][-30:]
    
    save_version_history(history)
    
    return has_update, current_version, latest_version

if __name__ == "__main__":
    has_update, current, latest = main()
    # 返回退出码：0 = 无更新，1 = 有更新
    sys.exit(1 if has_update else 0)
