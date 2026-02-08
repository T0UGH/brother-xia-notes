# OpenCode Agent 系统深度分析

> 🔍 深入解析 OpenCode 的多 Agent 架构、权限控制与任务分配机制

---

## 一、架构概览

OpenCode 的 Agent 系统采用**分层权限 + 多角色协作**的设计，核心目标是在安全的前提下最大化 AI 的自动化能力。

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│                      (TUI / Desktop)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Session Manager                           │
│         (维护对话状态、历史记录、上下文窗口)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Router                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │
│  │  build  │  │  plan   │  │ general │  │   explore   │  │
│  │(主代理) │  │(只读)   │  │(子代理) │  │ (代码探索)  │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Permission Engine                         │
│         (规则匹配、路径通配、权限决策)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Tool Registry                            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐  │
│  │ read │ │ edit │ │ bash │ │ grep │ │ glob │ │ web*   │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心 Agent 详解

### 2.1 build（默认主代理）

```typescript
{
  name: "build",
  mode: "primary",
  native: true,
  description: "The default agent. Executes tools based on configured permissions.",
  permission: {
    "*": "allow",              // 默认允许所有
    "doom_loop": "ask",        // 死循环检测需询问
    "external_directory": "ask", // 外部目录访问需询问
    "question": "allow",         // 允许提问
    "plan_enter": "allow",       // 允许进入 plan 模式
  }
}
```

**设计意图**：
- 作为默认代理，承担绝大多数开发任务
- 拥有完整工具权限，但关键危险操作需要用户确认
- 支持切换到 plan 模式进行安全分析

---

### 2.2 plan（只读规划模式）

```typescript
{
  name: "plan",
  mode: "primary",
  native: true,
  description: "Plan mode. Disallows all edit tools.",
  permission: {
    "*": "deny",                    // 默认拒绝所有
    "question": "allow",            // 允许提问
    "plan_exit": "allow",           // 允许退出 plan 模式
    "external_directory": {
      [path.join(dataDir, "plans", "*")]: "allow"
    },
    "edit": {
      "*": "deny",                   // 默认禁止编辑
      // 但允许编辑计划目录下的文件
      [path.join(".opencode", "plans", "*.md")]: "allow",
      [path.join(dataDir, "plans", "*.md")]: "allow"
    }
  }
}
```

**设计亮点**：
- **创新的半只读模式**：禁止全局编辑，但允许在专门的计划目录做笔记
- 用户可以安全地探索代码、制定计划，然后在 plan 目录下记录方案
- 退出 plan 模式后可执行实际操作

---

### 2.3 general（通用子代理）

```typescript
{
  name: "general",
  mode: "subagent",
  native: true,
  description: "General-purpose agent for researching complex questions and executing multi-step tasks.",
  permission: {
    // 继承默认权限
    "todoread": "deny",   // 禁止读取 todo
    "todowrite": "deny",  // 禁止写入 todo
  }
}
```

**用途**：
- 通过 `@general` 调用
- 并行执行多个研究任务
- 不能访问主会话的 todo 列表（隔离性）

---

### 2.4 explore（代码探索专用）

```typescript
{
  name: "explore",
  mode: "subagent",
  native: true,
  description: "Fast agent specialized for exploring codebases.",
  prompt: PROMPT_EXPLORE,  // 专门的探索 prompt
  permission: {
    "*": "deny",         // 默认全拒绝
    // 只允许只读工具
    "grep": "allow",
    "glob": "allow",
    "list": "allow",
    "bash": "allow",     // 但限制只读操作
    "webfetch": "allow",
    "websearch": "allow",
    "codesearch": "allow",
    "read": "allow",
    "external_directory": {
      [Truncate.GLOB]: "allow"
    }
  }
}
```

**专用设计**：
- 只能使用只读工具（read/grep/glob/list）
- 专门的 prompt 训练它成为文件搜索专家
- 支持按 thoroughness 级别搜索（quick/medium/very thorough）

---

## 三、权限系统详解

### 3.1 规则结构

```typescript
interface Rule {
  permission: string;   // 工具名：read/edit/bash/grep...
  pattern: string;      // 路径模式：*、*.md、/path/to/*
  action: "allow" | "deny" | "ask";
}

type Ruleset = Rule[];
```

### 3.2 匹配优先级

规则按**定义顺序**匹配，**第一个匹配的规则生效**。

```typescript
// 示例：plan agent 的 edit 权限
"edit": {
  "*": "deny",                           // 1. 默认禁止所有编辑
  ".opencode/plans/*.md": "allow",        // 2. 但允许编辑计划目录
  "/data/plans/*.md": "allow"             // 3. 以及数据目录的计划
}
// 匹配顺序：先检查具体路径，再 fallback 到 *
```

### 3.3 配置合并策略

```typescript
// 三层合并
const effectiveRuleset = PermissionNext.merge(
  defaults,     // 系统默认权限
  agentSpecific, // agent 特定权限
  userConfig     // 用户自定义配置
);

// 同权限、同 pattern 的规则会覆盖，不是追加
```

### 3.4 实际评估流程

```typescript
function evaluate(
  permission: string,    // 如 "edit"
  path: string,          // 如 "/home/user/project/src/main.ts"
  ruleset: Ruleset       // agent 的规则列表
): { action: Action, rule?: Rule } {
  // 按顺序遍历规则，找到第一个匹配的
  for (const rule of ruleset) {
    if (Wildcard.match(permission, rule.permission) && 
        Wildcard.match(path, rule.pattern)) {
      return { action: rule.action, rule };
    }
  }
  // 默认 deny（安全原则）
  return { action: "deny" };
}
```

---

## 四、Agent 切换机制

### 4.1 Tab 键切换

```
用户按 Tab → TUI 显示可用 primary agent 列表 → 选择后切换
```

### 4.2 子代理调用

```typescript
// 通过 @agent 语法调用
const response = await session.invoke("@explore find all API routes in this codebase");

// 子代理执行过程：
// 1. 创建隔离的会话上下文
// 2. 加载子代理的权限配置
// 3. 执行工具调用链
// 4. 返回结果给父会话
```

### 4.3 Plan 模式转换

```
在 build agent 中：
用户输入 → 检测到 "plan" 指令或按特定快捷键 → 切换到 plan agent

plan agent 特性：
- 所有编辑操作被拒绝
- 允许在 .opencode/plans/*.md 做笔记
- 可随时退出回到 build 模式执行
```

---

## 五、设计思想总结

### 5.1 安全优先

- **默认拒绝**：没有明确允许的操作都被拒绝
- **渐进授权**：从只读(plan)到完全访问(build)，权限逐步开放
- **路径隔离**：限制特定目录的访问，防止意外操作

### 5.2 角色分离

- **主代理 vs 子代理**：primary 负责交互，subagent 处理专项任务
- **可见 vs 隐藏**：用户可见的交互代理 vs 后台工作的系统代理
- **通用 vs 专用**：general 全能型 vs explore 专精型

### 5.3 可扩展性

- **配置即代码**：JSON/YAML 配置即可创建新 agent
- **Markdown 定义**：frontmatter 语法让 agent 定义更友好
- **权限继承**：基于规则的权限系统，组合灵活

---

## 六、与 OpenClaw 的对比

| 维度 | OpenCode | OpenClaw |
|------|----------|----------|
| **Agent 模型** | 内置多角色 + 用户自定义 | 单 agent + 用户 session |
| **权限系统** | 细粒度规则引擎 | 基于 capabilities 声明 |
| **模式切换** | Tab 键切换 build/plan | 通过指令切换模式 |
| **子代理** | 内置 explore/general | 支持 sessions_spawn |
| **配置方式** | JSON/Markdown/代码 | 主要 YAML 配置 |

---

*分析完成于 2026-02-08 by 🦐 虾哥*
