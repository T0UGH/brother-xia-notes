# Subagent Skills 调研报告

> 调研目标：找出是否有专门用于创建 subagent 的 skills，以及相关的最佳实践

---

## 核心发现

### 🔍 现状：没有专门的 "Subagent Creator" Skill

经过全面调研，**目前 Clawdbot 生态系统中没有专门用于"创建 subagent"的独立 skill**。

但这并不意味着无法创建 subagent —— 实际上，Clawdbot **原生支持** `sessions_spawn` 工具，可以直接使用。

---

## 现有相关 Skills

### 1. **skill-creator** ⭐ 最相关
```yaml
name: skill-creator
description: Create or update AgentSkills. Use when designing, structuring, or packaging skills with scripts, references, and assets.
```

**作用**：这是创建任何 skill（包括 subagent 相关 skill）的官方指南。

**关键内容**：
- Skill 的结构（SKILL.md + scripts/ + references/ + assets/）
- 创建流程（6步：理解 → 规划 → 初始化 → 编辑 → 打包 → 迭代）
- Progressive Disclosure 设计原则

**位置**：`/Users/haha/.npm-global/lib/node_modules/clawdbot/skills/skill-creator/SKILL.md`

---

### 2. **coding-agent** - 运行 Coding Agent 的参考
```yaml
name: coding-agent
description: Run Codex CLI, Claude Code, OpenCode, or Pi Coding Agent via background process for programmatic control.
```

**作用**：展示了如何通过 `bash` 工具在后台运行 coding agents。

**关键启示**：
- 使用 `pty:true` 参数（伪终端）来运行交互式 CLI 工具
- 使用 `background:true` 实现后台运行
- 使用 `process` 工具监控和管理后台会话

**这与 subagent 的关系**：subagent 本质上也是后台运行的独立会话，模式非常相似。

---

### 3. **session-logs** - 会话日志分析
```yaml
name: session-logs
description: Search and analyze your own session logs (older/parent conversations) using jq.
```

**作用**：搜索和分析历史会话记录。

**与 subagent 的关系**：可以用来追踪 subagent 的活动记录。

---

## 原生创建 Subagent 的方法

### 核心工具：`sessions_spawn`

Clawdbot 原生提供 `sessions_spawn` 工具来创建 subagent。

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `task` | string | (required) | Subagent 要执行的任务 |
| `label` | string | — | 简短标签，用于识别 |
| `agentId` | string | (caller’s agent) | 在哪个 agent 下 spawn |
| `model` | string | (optional) | 覆盖默认模型 |
| `thinking` | string | (optional) | 覆盖思考级别 |
| `runTimeoutSeconds` | number | 0 (no limit) | N 秒后终止 subagent |
| `cleanup` | "delete" \| "keep" | "keep" | "delete" 立即归档 |

**使用示例**：

```bash
# 基本用法 - 研究一个主题
sessions_spawn:
  task: "Research the latest Node.js release notes and summarize key features"
  label: "nodejs-research"

# 指定模型和超时
sessions_spawn:
  task: "Analyze the codebase and find performance bottlenecks"
  label: "perf-analysis"
  model: "anthropic/claude-opus-4"
  runTimeoutSeconds: 300
  cleanup: "delete"
```

---

### 管理 Subagent

**查看所有 subagent**：
```bash
/subagents list
```

**停止 subagent**：
```bash
/subagents stop <label-or-id>
```

**监控后台会话**（使用 `process` 工具）：
```bash
# 列出所有会话
process action:list

# 查看特定会话的日志
process action:log sessionId:xxx

# 发送输入到会话
process action:submit sessionId:xxx data:"yes"

# 终止会话
process action:kill sessionId:xxx
```

---

## 是否需要创建专门的 "Subagent" Skill？

### 分析

**当前状况**：
- ✅ `sessions_spawn` 工具原生支持，无需 skill 即可使用
- ✅ `skill-creator` 提供了创建任何 skill 的指南
- ❌ 没有专门封装 subagent 最佳实践的 skill

**潜在价值**：

一个专门的 **"subagent-manager"** 或 **"parallel-worker"** skill 可以：

1. **封装常见模式**：
   - 批量任务并行处理（如同时分析多个文件）
   - Map-Reduce 模式（多个 subagent 收集数据，一个汇总）
   - 竞赛模式（多个 subagent 尝试不同方案，选最优）

2. **提供便捷命令**：
   ```bash
   /parallel:research "topic" --agents 3
   /parallel:analyze files/*.js --agents 5
   /parallel:mapreduce --mapper "extract data" --reducer "summarize"
   ```

3. **内置最佳实践**：
   - 自动处理 subagent 超时和重试
   - 结果合并和冲突解决策略
   - 成本控制和预算限制

### 结论

| 方案 | 适用场景 | 复杂度 |
|------|----------|--------|
| **直接使用 `sessions_spawn`** | 偶尔使用，简单任务 | ⭐ |
| **创建一个轻量级 "subagent-helper" skill** | 频繁使用，需要便捷命令 | ⭐⭐ |
| **创建一个完整的 "parallel-workflow" skill** | 复杂的并行工作流，需要 Map-Reduce 等高级模式 | ⭐⭐⭐ |

**建议**：
- 如果平哥当前需求是**简单、偶尔**使用 subagent → 直接使用 `sessions_spawn` 即可
- 如果需要**频繁、批量**使用 → 建议创建一个轻量级 skill 封装常见模式

---

## 参考资源

1. **OpenClaw 官方文档 - Sub-Agents**：https://docs.openclaw.ai/tools/subagents
2. **Clawdbot Sub-agents 并行任务执行指南**：https://zenvanriel.nl/ai-engineer-blog/clawdbot-subagents-parallel-tasks-guide/
3. **Awesome Clawdbot Skills**：https://github.com/VoltAgent/awesome-clawdbot-skills

---

*报告生成时间：2026-02-10*
