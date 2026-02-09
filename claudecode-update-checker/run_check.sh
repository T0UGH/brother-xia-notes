#!/bin/bash
# Claude Code 更新检查脚本

# 设置代理
export HTTP_PROXY=http://127.0.0.1:1087
export HTTPS_PROXY=http://127.0.0.1:1087

# 检查脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 运行检查脚本
python3 check_update.py

# 获取退出码
EXIT_CODE=$?

# 如果有更新，发送通知
if [ $EXIT_CODE -eq 1 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎉 发现 Claude Code 更新！"
    
    # 如果有 webhook 或通知工具，可以在这里添加
    # 例如：发送 Feishu 通知、Email 等
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Claude Code 已是最新版本或检查失败"
fi

exit $EXIT_CODE
