# OpenCode 工具系统深度分析

> 🔧 从注册机制到并行执行，全面解析 OpenCode 的工具调用架构

---

## 一、架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         LLM Layer                                │
│              (生成工具调用 JSON / function calling)               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tool Registry                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Native    │  │   Plugin    │  │   Custom    │            │
│  │   Tools     │  │   Tools     │  │   Tools     │            │
│  │  (内置20+)  │  │  (MCP/sdk)  │  │  (用户定义) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Execution Engine                            │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  Single Tool    │    │   Batch Tool    │    │   Stream    │ │
│  │  (同步执行)      │    │  (并行25个)      │    │  (实时输出) │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Permission & Safety Layer                   │   │
│  │  (路径检查 / 权限验证 / 超时控制 / 沙箱限制)              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、工具定义与注册

### 2.1 Tool.define - 工厂模式

```typescript
// 核心工厂函数
export function Tool.define<Parameters extends ZodType, Result extends Metadata>(
  id: string,
  init: Info["init"] | Awaited<ReturnType<Info["init"]>>
): Info<Parameters, Result> {
  return {
    id,
    init: async (initCtx) => {
      const toolInfo = init instanceof Function ? await init(initCtx) : init
      const execute = toolInfo.execute
      
      // 包装 execute 函数，添加参数验证和截断处理
      toolInfo.execute = async (args, ctx) => {
        // 1. 参数验证（Zod schema）
        try {
          toolInfo.parameters.parse(args)
        } catch (error) {
          if (error instanceof ZodError && toolInfo.formatValidationError) {
            throw new Error(toolInfo.formatValidationError(error), { cause: error })
          }
          throw new Error(`Invalid arguments for ${id}: ${error}`)
        }
        
        // 2. 执行工具逻辑
        const result = await execute(args, ctx)
        
        // 3. 输出截断处理（防止超出上下文限制）
        if (result.metadata.truncated !== undefined) {
          return result  // 工具自己处理截断
        }
        const truncated = await Truncate.output(result.output, {}, initCtx?.agent)
        return {
          ...result,
          output: truncated.content,
          metadata: {
            ...result.metadata,
            truncated: truncated.truncated,
            ...(truncated.truncated && { outputPath: truncated.outputPath }),
          },
        }
      }
      return toolInfo
    },
  }
}
```

### 2.2 内置工具清单

| 工具 | 用途 | 权限敏感 | 特殊说明 |
|------|------|----------|----------|
| `read` | 读取文件 | ✅ 路径检查 | 支持行范围读取 |
| `edit` | 编辑文件 | ✅ 权限验证 | 基于 diff 的精确替换 |
| `write` | 写入文件 | ✅ 路径检查 | 创建或覆盖 |
| `bash` | 执行命令 | ✅ 严格限制 | 超时控制 (默认2分钟) |
| `grep` | 文本搜索 | ❌ | 支持 regex |
| `glob` | 文件匹配 | ❌ | 批量查找 |
| `webfetch` | 网页获取 | ✅ 需权限 | 自动提取内容 |
| `websearch` | 网络搜索 | ✅ 需权限 | 集成搜索 API |
| `codesearch` | 代码搜索 | ✅ 需权限 | 语义搜索 |
| `task` | 创建任务 | ✅ | 子任务管理 |
| `todoread/todowrite` | 待办管理 | ✅ 按 agent | 仅主代理可用 |
| `batch` | 批量执行 | ✅ | 并行 25 个工具 |
| `skill` | 调用技能 | ✅ | 动态加载 |
| `apply_patch` | 应用补丁 | ✅ | 类似 git apply |
| `lsp` | 语言服务 | ✅ | 代码分析补全 |
| `plan_enter/plan_exit` | 模式切换 | ✅ | plan 模式控制 |

---

## 三、核心工具详解

### 3.1 edit 工具 - 智能文件编辑

**核心挑战**：如何让 LLM 可靠地编辑文件，而不是直接覆盖整个文件？

**OpenCode 的方案**：基于 `oldString` → `newString` 的 diff 替换

```typescript
export const EditTool = Tool.define("edit", {
  description: DESCRIPTION,  // 详细的工具说明
  parameters: z.object({
    filePath: z.string().describe("The absolute path to the file to modify"),
    oldString: z.string().describe("The text to replace"),
    newString: z.string().describe("The text to replace it with (must be different)"),
    replaceAll: z.boolean().optional().describe("Replace all occurrences (default false)"),
  }),
  
  async execute(params, ctx) {
    // 1. 参数验证
    if (params.oldString === params.newString) {
      throw new Error("oldString and newString must be different")
    }
    
    // 2. 路径解析和安全检查
    const filePath = path.isAbsolute(params.filePath) 
      ? params.filePath 
      : path.join(Instance.directory, params.filePath)
    
    // 检查是否在允许的外部目录
    await assertExternalDirectory(ctx, filePath)
    
    // 3. 文件锁定（防止并发修改）
    await FileTime.withLock(filePath, async () => {
      // 4. 读取当前内容
      const file = Bun.file(filePath)
      const stats = await file.stat().catch(() => {})
      if (!stats) throw new Error(`File ${filePath} not found`)
      if (stats.isDirectory()) throw new Error(`Path is a directory: ${filePath}`)
      
      // 5. 时间戳检查（防止文件在我们读取前被修改）
      await FileTime.assert(ctx.sessionID, filePath)
      
      const contentOld = await file.text()
      
      // 6. 执行替换
      const contentNew = replace(contentOld, params.oldString, params.newString, params.replaceAll)
      
      // 7. 生成 diff（用于展示给用户）
      const diff = trimDiff(createTwoFilesPatch(
        filePath, filePath,
        normalizeLineEndings(contentOld),
        normalizeLineEndings(contentNew)
      ))
      
      // 8. 权限检查（询问用户是否允许）
      await ctx.ask({
        permission: "edit",
        patterns: [path.relative(Instance.worktree, filePath)],
        always: ["*"],
        metadata: { filepath: filePath, diff },
      })
      
      // 9. 写入文件
      await file.write(contentNew)
      
      // 10. 发布事件（通知文件系统观察者）
      await Bus.publish(File.Event.Edited, { file: filePath })
      await Bus.publish(FileWatcher.Event.Updated, { file: filePath, event: "change" })
      
      // 11. 更新时间戳记录
      FileTime.read(ctx.sessionID, filePath)
    })
  }
})
```

**设计亮点**：
1. **精确替换**：基于 `oldString` → `newString`，不是行号定位（避免行号漂移问题）
2. **并发安全**：文件锁 + 时间戳检查，防止竞态条件
3. **可视化确认**：生成 diff 给用户确认
4. **批量替换**：`replaceAll` 支持一键替换多处
5. **事件驱动**：修改后发布事件，UI 自动刷新

---

### 3.2 bash 工具 - 命令执行的安全沙箱

**核心挑战**：如何让用户执行任意命令，同时防止误操作和安全隐患？

```typescript
export const BashTool = Tool.define("bash", async () => {
  // 检测可用的 shell
  const shell = Shell.acceptable()
  
  return {
    description: DESCRIPTION
      .replaceAll("${directory}", Instance.directory)
      .replaceAll("${maxLines}", String(Truncate.MAX_LINES))
      .replaceAll("${maxBytes}", String(Truncate.MAX_BYTES)),
    
    parameters: z.object({
      command: z.string().describe("The command to execute"),
      timeout: z.number().optional().describe("Timeout in milliseconds"),
      workdir: z.string().optional().describe(
        `Working directory. Defaults to ${Instance.directory}. Use this instead of 'cd'.`
      ),
      description: z.string().describe(
        "Clear description of what this command does in 5-10 words"
      ),
    }),
    
    async execute(params, ctx) {
      const cwd = params.workdir || Instance.directory
      
      // 1. 参数验证
      if (params.timeout !== undefined && params.timeout < 0) {
        throw new Error(`Invalid timeout: ${params.timeout}`)
      }
      
      // 2. 超时设置（默认2分钟）
      const timeout = params.timeout ?? DEFAULT_TIMEOUT
      
      // 3. 解析命令，提取文件路径用于权限检查
      const tree = await parser().then((p) => p.parse(params.command))
      const directories = new Set<string>()
      const patterns = new Set<string>()
      
      // 4. 静态分析命令，提取危险操作
      for (const node of tree.rootNode.descendantsOfType("command")) {
        const command = extractCommand(node)
        
        // 检查危险命令（cd/rm/cp/mv/mkdir/touch 等）
        if (["cd", "rm", "cp", "mv", "mkdir", "touch"].includes(command[0])) {
          for (const arg of command.slice(1)) {
            // 解析参数中的路径
            const resolved = await resolvePath(arg, cwd)
            if (resolved && !Instance.containsPath(resolved)) {
              directories.add(path.dirname(resolved))
            }
          }
        }
        
        // 记录命令模式用于权限检查
        patterns.add(command.join(" ") + " *")
      }
      
      // 5. 权限检查
      if (directories.size > 0) {
        await ctx.ask({
          permission: "external_directory",
          patterns: Array.from(directories).map((d) => path.join(d, "*")),
          always: Array.from(patterns),
        })
      }
      
      // 6. 权限验证（bash 工具本身）
      await ctx.ask({
        permission: "bash",
        patterns: Array.from(patterns),
        always: [BashArity.prefix(extractedCommand).join(" ") + " *"],
      })
      
      // 7. 执行命令
      const abortController = new AbortController()
      const timeoutId = setTimeout(() => abortController.abort(), timeout)
      
      try {
        const result = await $({ 
          cwd, 
          signal: abortController.signal,
          env: process.env 
        })[shell](params.command).quiet()
        
        clearTimeout(timeoutId)
        
        // 8. 截断输出（防止超出上下文限制）
        const truncated = await Truncate.output(result.stdout(), {}, initCtx?.agent)
        
        return {
          title: params.description || params.command.slice(0, 50),
          output: truncated.content,
          metadata: {
            command: params.command,
            exitCode: result.exitCode,
            truncated: truncated.truncated,
            ...(truncated.truncated && { outputPath: truncated.outputPath }),
          },
        }
      } catch (error) {
        clearTimeout(timeoutId)
        throw error
      }
    },
  }
})
```

**安全设计亮点**：
1. **命令解析**：用 tree-sitter 解析 bash 语法，静态分析命令结构
2. **路径提取**：自动识别命令中的文件路径，检查是否在允许目录
3. **危险命令识别**：cd/rm/cp/mv 等命令会触发额外的权限检查
4. **超时控制**：默认2分钟超时，防止长时间挂起
5. **输出截断**：防止大输出撑爆上下文
6. **信号取消**：支持中断执行

---

### 3.3 batch 工具 - 并行执行引擎

**核心能力**：一次调用并行执行最多25个工具，大幅提升效率

```typescript
export const BatchTool = Tool.define("batch", async () => {
  // 禁止嵌套 batch（防止递归爆炸）
  const DISALLOWED = new Set(["batch"])
  
  return {
    description: DESCRIPTION,
    parameters: z.object({
      tool_calls: z
        .array(
          z.object({
            tool: z.string().describe("工具名"),
            parameters: z.object({}).loose().describe("工具参数"),
          })
        )
        .min(1, "至少提供一个工具调用")
        .max(25, "最多25个工具")  // 硬性限制
        .describe("要并行执行的工具调用数组"),
    }),
    
    async execute(params, ctx) {
      const { Session } = await import("../session")
      const { Identifier } = await import("../id/id")
      
      // 1. 获取可用工具列表
      const { ToolRegistry } = await import("./registry")
      const availableTools = await ToolRegistry.tools({ modelID: "", providerID: "" })
      const toolMap = new Map(availableTools.map((t) => [t.id, t]))
      
      // 2. 执行单个工具调用
      const executeCall = async (call: { tool: string; parameters: any }) => {
        const callStartTime = Date.now()
        const partID = Identifier.ascending("part")
        
        try {
          // 2.1 检查工具是否允许在 batch 中使用
          if (DISALLOWED.has(call.tool)) {
            throw new Error(`Tool '${call.tool}' is not allowed in batch`)
          }
          
          // 2.2 查找工具
          const tool = toolMap.get(call.tool)
          if (!tool) {
            throw new Error(`Tool '${call.tool}' not found`)
          }
          
          // 2.3 参数验证
          const validatedParams = tool.parameters.parse(call.parameters)
          
          // 2.4 更新会话状态为 running
          await Session.updatePart({
            id: partID,
            messageID: ctx.messageID,
            sessionID: ctx.sessionID,
            type: "tool",
            tool: call.tool,
            callID: partID,
            state: {
              status: "running",
              input: call.parameters,
              time: { start: callStartTime },
            },
          })
          
          // 2.5 执行工具
          const result = await tool.execute(validatedParams, { ...ctx, callID: partID })
          
          // 2.6 更新会话状态为 completed
          await Session.updatePart({
            id: partID,
            messageID: ctx.messageID,
            sessionID: ctx.sessionID,
            type: "tool",
            tool: call.tool,
            callID: partID,
            state: {
              status: "completed",
              input: call.parameters,
              output: result.output,
              title: result.title,
              metadata: result.metadata,
              attachments: result.attachments,
              time: { start: callStartTime, end: Date.now() },
            },
          })
          
          return { success: true, tool: call.tool, result }
          
        } catch (error) {
          // 2.7 更新会话状态为 error
          await Session.updatePart({
            id: partID,
            messageID: ctx.messageID,
            sessionID: ctx.sessionID,
            type: "tool",
            tool: call.tool,
            callID: partID,
            state: {
              status: "error",
              input: call.parameters,
              error: error instanceof Error ? error.message : String(error),
              time: { start: callStartTime, end: Date.now() },
            },
          })
          
          return { success: false, tool: call.tool, error }
        }
      }
      
      // 3. 并行执行所有工具
      const results = await Promise.all(params.tool_calls.map(executeCall))
      
      // 4. 生成执行摘要
      const successful = results.filter((r) => r.success).length
      const failed = results.length - successful
      
      return {
        title: `Batch execution (${successful}/${results.length} successful)`,
        output: failed > 0 
          ? `Executed ${successful}/${results.length} tools successfully. ${failed} failed.`
          : `All ${successful} tools executed successfully.\n\nKeep using the batch tool for optimal performance!`,
        metadata: {
          total: results.length,
          successful,
          failed,
          tools: params.tool_calls.map((c) => c.tool),
        },
      }
    },
  }
})
```

**设计亮点**：
1. **真正的并行**：`Promise.all()` 同时执行，不是串行
2. **完善的会话状态**：running → completed/error，UI 实时更新
3. **独立错误处理**：单个工具失败不影响其他工具
4. **硬性限制**：最多25个，防止资源耗尽
5. **智能建议**：成功时提示"继续使用 batch tool 以获得最佳性能"

---

## 四、安全与权限集成

### 4.1 权限检查流程

```
LLM 生成工具调用
       ↓
解析参数
       ↓
提取涉及的路径/命令
       ↓
遍历权限规则
       ↓
匹配? ──否──→ 默认 deny
       ↓ 是
   action = ?
       ↓
  ┌────┼────┐
 allow  deny  ask
   ↓     ↓     ↓
 执行  报错  询问用户
```

### 4.2 代码中的权限集成

```typescript
// 示例：bash 工具的权限检查
async execute(params, ctx) {
  // 1. 解析命令，提取路径
  const tree = await parser().then((p) => p.parse(params.command))
  const directories = new Set<string>()
  
  for (const node of tree.rootNode.descendantsOfType("command")) {
    const command = extractCommand(node)
    
    // 2. 检查危险命令
    if (["cd", "rm", "cp", "mv", "mkdir", "touch"].includes(command[0])) {
      for (const arg of command.slice(1)) {
        const resolved = await resolvePath(arg, cwd)
        if (resolved && !Instance.containsPath(resolved)) {
          directories.add(path.dirname(resolved))
        }
      }
    }
  }
  
  // 3. 外部目录权限检查
  if (directories.size > 0) {
    await ctx.ask({
      permission: "external_directory",
      patterns: Array.from(directories).map((d) => path.join(d, "*")),
      always: Array.from(patterns),
    })
  }
  
  // 4. bash 工具权限检查
  await ctx.ask({
    permission: "bash",
    patterns: Array.from(patterns),
    always: [BashArity.prefix(extractedCommand).join(" ") + " *"],
  })
  
  // 5. 执行命令...
}
```

---

## 五、与 OpenClaw 的对比

| 维度 | OpenCode | OpenClaw |
|------|----------|----------|
| **工具定义** | `Tool.define()` 工厂 + Zod schema | `tools:` 配置 + JSON schema |
| **工具数量** | 20+ 内置 + 插件 + 自定义 | 核心工具集 |
| **并行执行** | `batch` 工具（25个并行） | 依赖 LLM 并行调用 |
| **权限集成** | 细粒度规则引擎 | capabilities 声明 |
| **会话状态** | running/completed/error | 简单调用响应 |
| **输出截断** | 自动截断 + 溢出文件 | 依赖模型限制 |
| **插件扩展** | MCP / SDK / Markdown | 内置扩展机制 |

---

## 六、设计思想总结

### 6.1 核心理念

1. **安全优先**：所有危险操作都需权限验证，默认拒绝
2. **精确控制**：基于内容的 diff 替换，不是模糊的行号定位
3. **性能优化**：并行执行、自动截断、流式处理
4. **可扩展**：工厂模式 + 插件系统，易于添加新工具

### 6.2 关键创新

- **batch 工具**：真正的并行执行，不只是并发发起
- **edit 工具**：基于 `oldString/newString` 的精确替换
- **权限引擎**：细粒度规则 + 路径模式匹配
- **会话状态**：完整的生命周期管理（running → completed/error）

---

*分析完成于 2026-02-08 by 🦐 虾哥*
