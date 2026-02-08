# OpenCode 插件系统深度分析

> 🔌 从 Hook 机制到动态加载，全面解析 OpenCode 的可扩展架构

---

## 一、架构概览

### 1.1 核心设计理念

OpenCode 的插件系统采用 **Hook-based Architecture**（基于钩子的架构），灵感来源于：

- **WordPress Plugin System** - 事件驱动的钩子机制
- **Webpack Plugin System** - 编译时钩子
- **VS Code Extension API** - 生命周期管理

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenCode Core                          │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Agent    │  │    Tool     │  │    LSP      │        │
│  │   System    │  │   System    │  │   Client    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Plugin Hook Points                      │  │
│  │                                                      │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │  auth   │ │  tool   │ │ config  │ │  event  │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Plugin Ecosystem                       │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Internal  │  │   Built-in  │  │   External  │          │
│  │  (Codex,    │  │  (Anthropic │  │  (npm or   │          │
│  │  Copilot,   │  │   Auth)     │  │   file://)  │          │
│  │  GitLab)    │  │             │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、Hook 机制详解

### 2.1 Hooks 接口定义

```typescript
// packages/opencode/src/plugin/index.ts

export interface Hooks {
  /**
   * 认证钩子 - 用于自定义认证流程
   */
  auth?(input: {
    provider: string
    credentials: Record<string, string>
  }): Promise<{
    token: string
    expiresAt?: number
  }>

  /**
   * 工具钩子 - 用于注册自定义工具
   */
  tool?(input: {
    register: (tool: ToolDefinition) => void
    unregister: (toolId: string) => void
  }): void

  /**
   * 配置钩子 - 用于修改配置
   */
  config?(config: Config): Promise<void>

  /**
   * 事件钩子 - 用于监听系统事件
   */
  event?(input: { event: BusEvent }): Promise<void>

  /**
   * 转换钩子 - 用于修改模型输入/输出
   */
  transform?(input: {
    messages: ModelMessage[]
    model: Provider.Model
  }): Promise<{ messages: ModelMessage[] }>
}
```

### 2.2 Hook 触发机制

```typescript
// packages/opencode/src/plugin/index.ts

export async function trigger<
  Name extends Exclude<keyof Required<Hooks>, "auth" | "event" | "tool">,
  Input = Parameters<Required<Hooks>[Name]>[0],
  Output = Parameters<Required<Hooks>[Name]>[1],
>(
  name: Name,
  input: Input,
  output: Output
): Promise<Output> {
  // 遍历所有插件的指定 hook
  for (const hook of await state().then((x) => x.hooks)) {
    const fn = hook[name]
    if (!fn) continue
    // 顺序执行 hook
    await fn(input, output)
  }
  return output
}
```

### 2.3 Hook 执行流程

```
用户操作 / 系统事件
       ↓
┌─────────────────┐
│ 触发 Hook 点    │
│ (如: tool.execute)│
└────────┬────────┘
         ↓
┌─────────────────┐
│ 遍历所有插件     │
│ 查找对应 Hook   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 顺序执行 Hook   │
│ (可修改 input/output)│
└────────┬────────┘
         ↓
┌─────────────────┐
│ 返回最终结果    │
└─────────────────┘
```

---

## 三、插件类型详解

### 3.1 内置插件 (Internal)

```typescript
// packages/opencode/src/plugin/index.ts

const INTERNAL_PLUGINS: PluginInstance[] = [
  CodexAuthPlugin,      // OpenAI Codex 认证
  CopilotAuthPlugin,    // GitHub Copilot 认证
  GitlabAuthPlugin,     // GitLab 认证
]
```

**特点**：
- 直接内嵌在代码中
- 无需安装
- 随核心一起发布

### 3.2 内置插件 (Built-in)

```typescript
// packages/opencode/src/plugin/index.ts

const BUILTIN = [
  "opencode-anthropic-auth@0.0.13"  // Anthropic 认证插件
]
```

**特点**：
- 从 npm 自动安装
- 首次启动时下载
- 可禁用

### 3.3 外部插件 (External)

#### 3.3.1 配置方式

```json
// opencode.json
{
  "plugin": [
    "opencode-my-plugin",                    // npm 包
    "opencode-another-plugin@1.2.3",         // 指定版本
    "file:///path/to/local/plugin",          // 本地路径
    "github:user/repo"                       // GitHub 仓库
  ]
}
```

#### 3.3.2 插件目录结构

```
my-opencode-plugin/
├── package.json          # npm 包配置
├── src/
│   └── index.ts         # 插件入口
├── opencode-plugin.json  # 插件元数据（可选）
└── README.md
```

#### 3.3.3 插件入口示例

```typescript
// my-plugin/src/index.ts
import type { Plugin } from '@opencode-ai/plugin'

const myPlugin: Plugin = async (input) => {
  return {
    // 认证钩子
    async auth({ provider, credentials }) {
      if (provider === 'my-provider') {
        const token = await authenticate(credentials)
        return { token, expiresAt: Date.now() + 3600000 }
      }
    },

    // 工具钩子
    tool({ register, unregister }) {
      // 注册自定义工具
      register({
        id: 'my-tool',
        description: 'My custom tool',
        parameters: z.object({ query: z.string() }),
        async execute({ query }) {
          return `Result for: ${query}`
        }
      })
    },

    // 配置钩子
    async config(config) {
      // 修改配置
      config.mySetting = 'value'
    },

    // 事件钩子
    async event({ event }) {
      console.log('Event:', event.type)
    },

    // 转换钩子
    async transform({ messages, model }) {
      // 修改消息
      return { messages: messages.map(m => ({ ...m, modified: true })) }
    }
  }
}

export default myPlugin
```

---

## 四、插件加载机制

### 4.1 加载流程

```
OpenCode 启动
       ↓
┌─────────────────┐
│ 1. 加载内置插件  │
│ (Internal)      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 2. 加载配置插件  │
│ (Config.plugin) │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 3. 自动安装     │
│ (Built-in npm)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 4. 初始化 Hooks │
│ (顺序执行)      │
└────────┬────────┘
         ↓
      完成启动
```

### 4.2 代码实现

```typescript
// packages/opencode/src/plugin/index.ts

const state = Instance.state(async () => {
  const hooks: Hooks[] = []
  
  // 1. 加载内部插件
  for (const plugin of INTERNAL_PLUGINS) {
    log.info('loading internal plugin', { name: plugin.name })
    const init = await plugin(input)
    hooks.push(init)
  }
  
  // 2. 加载配置中的插件
  let plugins = config.plugin ?? []
  if (plugins.length) await Config.waitForDependencies()
  
  // 3. 添加内置插件（自动安装）
  if (!Flag.OPENCODE_DISABLE_DEFAULT_PLUGINS) {
    plugins = [...BUILTIN, ...plugins]
  }
  
  // 4. 加载每个插件
  for (let plugin of plugins) {
    // 解析插件路径（npm / file / github）
    if (!plugin.startsWith('file://')) {
      // npm 包，自动安装
      const lastAtIndex = plugin.lastIndexOf('@')
      const pkg = lastAtIndex > 0 ? plugin.substring(0, lastAtIndex) : plugin
      const version = lastAtIndex > 0 ? plugin.substring(lastAtIndex + 1) : 'latest'
      
      plugin = await BunProc.install(pkg, version)
    }
    
    // 导入插件
    const mod = await import(plugin)
    
    // 执行插件初始化函数
    for (const [name, fn] of Object.entries<Plugin>(mod)) {
      if (typeof fn !== 'function') continue
      const init = await fn(input)
      hooks.push(init)
    }
  }
  
  return { hooks, input }
})
```

---

## 五、与 MCP 的集成

### 5.1 MCP (Model Context Protocol)

OpenCode 除了自己的插件系统，还支持 **MCP** - 来自 Anthropic 的开放标准：

```
┌─────────────────────────────────────────┐
│            OpenCode Core                 │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │      Native Plugin System        │   │
│  │  (TypeScript/JavaScript)        │   │
│  └─────────────────────────────────┘   │
│                   ↓                       │
│  ┌─────────────────────────────────┐   │
│  │      MCP Adapter Layer          │   │
│  │  (Protocol Translation)         │   │
│  └─────────────────────────────────┘   │
│                   ↓                       │
│  ┌─────────────────────────────────┐   │
│  │      External MCP Servers       │   │
│  │  (Any Language / Process)         │   │
│  │  • file-system                  │   │
│  │  • github                       │   │
│  │  • postgres                     │   │
│  │  • ...                          │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 5.2 MCP vs Native Plugin

| 特性 | Native Plugin | MCP Server |
|------|--------------|-----------|
| **语言** | TypeScript/JavaScript | 任意语言 |
| **运行方式** | 同进程 | 独立进程 (stdio/sse) |
| **通信** | 直接函数调用 | JSON-RPC |
| **性能** | 更高 (无序列化) | 稍低 (有协议开销) |
| **隔离性** | 低 (同进程) | 高 (独立进程) |
| **生态** | OpenCode 专属 | 通用标准 (Anthropic) |

### 5.3 在 OpenCode 中使用 MCP

```json
// opencode.json
{
  "mcp": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allow"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
      }
    },
    "postgres": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/postgres", "postgresql://..."]
    }
  }
}
```

---

## 六、插件开发实战

### 6.1 完整示例：GitHub 状态插件

```typescript
// my-github-plugin/src/index.ts
import { Plugin, ToolDefinition } from '@opencode-ai/plugin'
import { z } from 'zod'

const GitHubPlugin: Plugin = async (input) => {
  const token = process.env.GITHUB_TOKEN
  
  if (!token) {
    console.warn('GITHUB_TOKEN not set, GitHub plugin disabled')
    return {}
  }

  return {
    // 自定义工具
    tool({ register, unregister }) {
      const tools: ToolDefinition[] = [
        {
          id: 'github-issues',
          description: 'List and search GitHub issues',
          parameters: z.object({
            repo: z.string().describe('Owner/repo format'),
            state: z.enum(['open', 'closed', 'all']).default('open'),
            limit: z.number().default(10)
          }),
          async execute({ repo, state, limit }) {
            const response = await fetch(
              `https://api.github.com/repos/${repo}/issues?state=${state}&per_page=${limit}`,
              { headers: { Authorization: `token ${token}` } }
            )
            const issues = await response.json()
            return {
              output: issues.map((i: any) => `#${i.number}: ${i.title}`).join('\n'),
              metadata: { count: issues.length }
            }
          }
        },
        
        {
          id: 'github-pr',
          description: 'Get pull request details',
          parameters: z.object({
            repo: z.string(),
            number: z.number()
          }),
          async execute({ repo, number }) {
            const response = await fetch(
              `https://api.github.com/repos/${repo}/pulls/${number}`,
              { headers: { Authorization: `token ${token}` } }
            )
            const pr = await response.json()
            return {
              output: `PR #${pr.number}: ${pr.title}\nState: ${pr.state}\nBy: ${pr.user.login}`,
              metadata: { pr }
            }
          }
        },
        
        {
          id: 'github-create-issue',
          description: 'Create a new GitHub issue',
          parameters: z.object({
            repo: z.string(),
            title: z.string(),
            body: z.string().optional(),
            labels: z.array(z.string()).optional()
          }),
          async execute({ repo, title, body, labels }) {
            const response = await fetch(
              `https://api.github.com/repos/${repo}/issues`,
              {
                method: 'POST',
                headers: {
                  Authorization: `token ${token}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title, body, labels })
              }
            )
            const issue = await response.json()
            return {
              output: `Created issue #${issue.number}: ${issue.html_url}`,
              metadata: { issue }
            }
          }
        }
      ]
      
      // 注册所有工具
      for (const tool of tools) {
        register(tool)
      }
    },

    // 配置钩子
    async config(config) {
      // 添加 GitHub 相关的默认配置
      config.github = {
        ...config.github,
        defaultRepo: config.github?.defaultRepo || process.env.GITHUB_DEFAULT_REPO
      }
    },

    // 事件钩子
    async event({ event }) {
      // 监听系统事件
      if (event.type === 'session.start') {
        console.log('New session started, GitHub plugin active')
      }
      if (event.type === 'tool.execute' && event.tool === 'github-issues') {
        // 记录 GitHub API 调用
        console.log('GitHub API called:', event)
      }
    },

    // 转换钩子（修改 LLM 消息）
    async transform({ messages, model }) {
      // 在最后一条用户消息前添加 GitHub 上下文
      const lastUserIndex = messages.findLastIndex(m => m.role === 'user')
      if (lastUserIndex !== -1) {
        messages.splice(lastUserIndex, 0, {
          role: 'system',
          content: 'GitHub plugin is active. Available tools: github-issues, github-pr, github-create-issue'
        })
      }
      return { messages }
    }
  }
}

export default GitHubPlugin
```

---

## 七、插件打包与发布

### 7.1 目录结构

```
my-opencode-plugin/
├── package.json              # npm 包配置
├── tsconfig.json             # TypeScript 配置
├── src/
│   └── index.ts             # 插件入口
├── opencode-plugin.json      # 插件元数据
├── README.md                 # 文档
└── LICENSE                   # 许可证
```

### 7.2 package.json

```json
{
  "name": "my-opencode-plugin",
  "version": "1.0.0",
  "description": "My OpenCode plugin",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "prepublishOnly": "npm run build"
  },
  "keywords": ["opencode", "plugin"],
  "peerDependencies": {
    "@opencode-ai/plugin": "^1.0.0",
    "zod": "^3.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

### 7.3 元数据文件

```json
// opencode-plugin.json
{
  "name": "my-plugin",
  "displayName": "My Plugin",
  "description": "Does awesome things",
  "version": "1.0.0",
  "author": "Your Name",
  "license": "MIT",
  "homepage": "https://github.com/you/my-plugin",
  "repository": {
    "type": "git",
    "url": "https://github.com/you/my-plugin.git"
  },
  "bugs": {
    "url": "https://github.com/you/my-plugin/issues"
  },
  "categories": ["productivity", "integration"],
  "keywords": ["github", "api", "integration"],
  "activationEvents": [
    "onCommand:myPlugin.doSomething",
    "onFile:*.md"
  ],
  "contributes": {
    "commands": [
      {
        "command": "myPlugin.doSomething",
        "title": "Do Something",
        "category": "My Plugin"
      }
    ],
    "keybindings": [
      {
        "command": "myPlugin.doSomething",
        "key": "ctrl+shift+m",
        "when": "isFocused"
      }
    ],
    "configuration": {
      "title": "My Plugin",
      "properties": {
        "myPlugin.enabled": {
          "type": "boolean",
          "default": true,
          "description": "Enable My Plugin"
        },
        "myPlugin.apiKey": {
          "type": "string",
          "default": "",
          "description": "API Key for external service"
        }
      }
    }
  },
  "engines": {
    "opencode": ">=1.0.0"
  }
}
```

---

## 八、最佳实践

### 8.1 开发建议

```typescript
// 1. 始终使用 zod 验证输入
const MyToolSchema = z.object({
  query: z.string().min(1).max(1000),
  limit: z.number().min(1).max(100).default(10)
})

// 2. 提供详细的错误信息
async execute(params) {
  try {
    const result = await api.call(params)
    return {
      output: formatResult(result),
      metadata: { count: result.length }
    }
  } catch (error) {
    throw new Error(
      `API call failed: ${error.message}\n` +
      `Query: ${params.query}\n` +
      `Suggestion: Check API key or try again later`
    )
  }
}

// 3. 尊重用户配置
async config(config) {
  // 读取用户配置
  const myConfig = config.myPlugin || {}
  
  // 使用默认值
  const timeout = myConfig.timeout || 5000
  const retries = myConfig.retries || 3
  
  // 存储配置供后续使用
  this.config = { timeout, retries }
}

// 4. 清理资源
async destroy() {
  // 关闭连接
  await this.client.close()
  
  // 清理缓存
  this.cache.clear()
  
  // 取消订阅
  this.subscriptions.forEach(sub => sub.unsubscribe())
}
```

### 8.2 安全建议

```typescript
// 1. 永远不要硬编码密钥
// ❌ 错误
const API_KEY = 'sk-abc123...'

// ✅ 正确
const API_KEY = process.env.MY_PLUGIN_API_KEY

// 2. 验证所有输入
async execute(params) {
  // 使用 zod 验证
  const validated = MySchema.parse(params)
  
  // 额外安全检查
  if (validated.command.includes('rm -rf /')) {
    throw new Error('Dangerous command detected')
  }
  
  // ...
}

// 3. 限制资源使用
async execute(params) {
  // 超时控制
  const timeout = setTimeout(() => {
    throw new Error('Execution timeout')
  }, 30000)
  
  try {
    const result = await doWork(params)
    return result
  } finally {
    clearTimeout(timeout)
  }
}
```

---

## 九、与 OpenClaw 对比

| 维度 | OpenCode 插件系统 | OpenClaw 插件系统 |
|------|------------------|------------------|
| **架构** | Hook-based | 配置驱动 |
| **语言** | TypeScript/JavaScript | 多语言支持 |
| **运行方式** | 同进程 | 独立进程 |
| **通信** | 直接调用 | JSON-RPC / HTTP |
| **生态** | OpenCode 专属 | 通用标准 (MCP) |
| **安装方式** | npm / file / github | 配置加载 |
| **Hook 点** | 7+ 个 (auth/tool/config/event/...) | 事件驱动 |
| **权限控制** | 细粒度权限 | capabilities |
| **热更新** | 支持 | 支持 |
| **调试支持** | 内置日志 | 日志 + 调试器 |

---

## 十、总结

OpenCode 的插件系统展现了**现代可扩展架构**的设计思想：

1. **Hook-based Architecture** - 事件驱动的扩展点，松耦合
2. **多层插件类型** - Internal / Built-in / External 满足不同场景
3. **MCP 兼容** - 支持行业标准协议，生态互通
4. **完整生命周期** - 加载 → 初始化 → 执行 → 销毁
5. **安全设计** - 权限控制、资源限制、输入验证

这就是 OpenCode 能在保持核心简洁的同时，拥有丰富生态的秘诀！

---

*分析完成于 2026-02-08 by 🦐 虾哥*
