# MEMORY.md - Long-Term Memory

## System Configuration

### 1. Node.js TLS 配置（LaunchAgents 设置）
**来源**: 平哥 2026-02-09 设定  
**文件**: `/Users/haha/Library/LaunchAgents/com.clawdbot.gateway.plist`

该文件中必须包含以下配置来禁用 Node.js 的 SSL 证书验证：
```xml
<key>NODE_TLS_REJECT_UNAUTHORIZED</key>
<string>0</string>
</dict>
```

**用途**: 解决某些网络环境下 Node.js 的 SSL/TLS 连接问题。

---

### 2. GitHub/NPM 代理设置（中国访问）
**来源**: 平哥 2026-02-09 设定  
**原则**: 临时设置，用完即走（不写入 shell 配置文件）

在中国访问 GitHub 或使用 npm 下载仓库时，需要临时设置代理：
```bash
export http_proxy=http://127.0.0.1:1087
export https_proxy=http://127.0.0.1:1087
```

**使用方式示例**:
```bash
export http_proxy=http://127.0.0.1:1087 && export https_proxy=http://127.0.0.1:1087 && gh repo clone owner/repo
```

**注意**: 
- 不修改 `~/.bashrc`、`.zshrc` 等全局配置
- 每次需要时临时设置，用完失效

---

## 3. 数字花园 - brother-xia-notes 仓库

**来源**: 平哥与虾哥的约定（2026-02-09 明确）  
**路径**: `/Users/haha/.openclaw/workspace/brother-xia-notes`  
**GitHub 仓库**: 平哥的数字花园，存放虾哥写的所有重要 Markdown 文档

### 规则
- **虾哥写的所有重要文档**都必须同步到这个仓库
- 仓库是平哥的 **GitHub 数字花园**，用于沉淀知识
- 提交时使用规范的 commit message

### 当前已存放的文档
- `openclaw-memory-analysis.md` - OpenClaw 内存分析
- `opencode-*-analysis.md` (5个) - Opencode 各类分析
- `superpowers分析.md` - Superpowers 项目分析
- `clawdbot-memory.md` - Clawdbot 系统配置记忆（刚添加）

---

*Last updated: 2026-02-09*
