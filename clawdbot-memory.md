# Clawdbot 系统配置记忆

> 平哥与虾哥约定的系统配置，由虾哥维护

---

## 1. Node.js TLS 配置（LaunchAgents 设置）

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

## 2. GitHub/NPM 代理设置（中国访问）

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

*Last updated: 2026-02-09 by 虾哥 🦐*
