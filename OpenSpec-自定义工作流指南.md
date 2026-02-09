# OpenSpec 自定义工作流完全指南

> 本文档详细介绍 OpenSpec 的自定义工作流机制，帮助团队根据自身需求定制开发流程。

---

## 目录

1. [概述](#概述)
2. [三层自定义机制](#三层自定义机制)
3. [核心概念：Schema](#核心概念schema)
4. [实战：创建自定义工作流](#实战创建自定义工作流)
5. [高级用法](#高级用法)
6. [最佳实践](#最佳实践)

---

## 概述

OpenSpec 是一个轻量级的 AI 驱动规格框架，核心理念是**"在写代码前先达成一致"**。它通过结构化的变更流程（Changes）帮助团队管理需求、设计和实现。

**默认工作流（spec-driven）：**

```
proposal（提案）→ specs（规格）→ design（设计）→ tasks（任务）→ implement（实现）
```

但当团队有独特需求时，OpenSpec 提供了强大的**自定义工作流**能力。

---

## 三层自定义机制

OpenSpec 提供三个层级的自定义，从简单到复杂：

| 层级 | 机制 | 适用场景 | 复杂度 |
|------|------|----------|--------|
| **Level 1** | 项目配置 (`config.yaml`) | 设置默认值、注入上下文、添加规则 | ⭐ |
| **Level 2** | 自定义 Schemas | 定义全新的工作流产物和依赖关系 | ⭐⭐⭐ |
| **Level 3** | 全局覆盖 | 跨项目共享 Schemas | ⭐⭐ |

---

### Level 1: 项目配置

通过 `openspec/config.yaml` 快速自定义，无需创建新的 Schema。

**示例：**

```yaml
# openspec/config.yaml
schema: spec-driven  # 设置默认 schema

# 注入项目上下文（会出现在所有 AI 提示中）
context: |
  Tech stack: TypeScript, React, Node.js, PostgreSQL
  API style: RESTful, documented in docs/api.md
  Testing: Jest + React Testing Library
  We value backwards compatibility for all public APIs

# 针对特定产物的规则
rules:
  proposal:
    - Include rollback plan
    - Identify affected teams
  specs:
    - Use Given/When/Then format
    - Reference existing patterns before inventing new ones
  design:
    - Include performance considerations
    - Document error handling strategy
```

**原理：**

当生成任何产物时，OpenSpec 会将 `context` 和对应 `rules` 注入 AI 提示：

```xml
<context>
Tech stack: TypeScript, React, Node.js, PostgreSQL
...
</context>

<rules>
- Include rollback plan
- Identify affected teams
</rules>

<template>
[Schema's built-in template]
</template>
```

---

### Level 2: 自定义 Schemas

当项目配置无法满足需求时，创建全新的 Schema。这是 OpenSpec 最强大的自定义能力。

**文件结构：**

```text
your-project/
├── openspec/
│   ├── config.yaml         # 项目配置
│   ├── schemas/            # 自定义 schemas 目录
│   │   └── my-workflow/    # 你的自定义工作流
│   │       ├── schema.yaml # 工作流定义
│   │       └── templates/  # 产物模板
│   │           ├── proposal.md
│   │           ├── spec.md
│   │           ├── design.md
│   │           └── tasks.md
│   └── changes/            # 变更目录
└── src/
```

---

## 核心概念：Schema

### Schema 结构详解

Schema 通过 `schema.yaml` 定义工作流的**产物（Artifacts）**及其**依赖关系**。

```yaml
# openspec/schemas/my-workflow/schema.yaml
name: my-workflow          # Schema 名称（唯一标识）
version: 1                 # 版本号
description: |            # 描述
  我的团队自定义工作流，适合快速迭代项目

# ============================================
# 产物定义（核心）
# ============================================
artifacts:
  # ------------------------------------------
  # 产物 1: 提案（Proposal）
  # ------------------------------------------
  - id: proposal              # 唯一标识符
    generates: proposal.md    # 生成的文件名
    description: 初始提案文档  # 人类可读描述
    template: proposal.md     # 使用的模板文件（在 templates/ 目录）
    
    # AI 生成该产物时的指令
    instruction: |
      创建一个提案文档，解释 WHY - 为什么要做这个变更。
      聚焦在问题本身，而不是解决方案。
      必须包含：
      1. 问题背景
      2. 期望 outcome
      3. 不做的影响
    
    requires: []  # 无依赖，这是工作流的起点

  # ------------------------------------------
  # 产物 2: 规格（Specs）
  # ------------------------------------------
  - id: specs
    generates: specs/*.md     # 支持 glob 模式，可生成多个文件
    description: 详细规格文档
    template: spec.md
    
    instruction: |
      基于提案创建详细规格，解释 WHAT - 要构建什么。
      必须包含：
      1. 功能需求（Given/When/Then 格式）
      2. 非功能需求（性能、安全）
      3. 边界情况和错误场景
    
    requires:
      - proposal  # 必须先有 proposal

  # ------------------------------------------
  # 产物 3: 设计（Design）
  # ------------------------------------------
  - id: design
    generates: design.md
    description: 技术设计文档
    template: design.md
    
    instruction: |
      创建技术设计文档，解释 HOW - 如何实现。
      必须包含：
      1. 架构图/流程图
      2. 关键组件和接口
      3. 数据模型
      4. 技术选型理由
    
    requires:
      - proposal
      - specs   # 可以同时依赖多个产物

  # ------------------------------------------
  # 产物 4: 任务（Tasks）
  # ------------------------------------------
  - id: tasks
    generates: tasks.md
    description: 实现任务清单
    template: tasks.md
    
    instruction: |
      基于设计创建实现任务清单。
      每个任务必须是：
      1. 可独立完成的
      2. 可验证的（有明确的 done 标准）
      3. 有预估时间（可选）
    
    requires:
      - design

# ============================================
# 执行配置（Apply 阶段）
# ============================================
apply:
  requires: [tasks]      # 执行 tasks 需要什么前置产物
  tracks: tasks.md      # 跟踪哪个文件的完成状态
```

---

### 关键字段详解

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 产物的唯一标识符，用于依赖引用 |
| `generates` | string | 生成的文件名，支持 glob（如 `specs/**/*.md`） |
| `description` | string | 人类可读的描述 |
| `template` | string | 模板文件名（位于 `templates/` 目录） |
| `instruction` | string | AI 生成该产物时的指令 |
| `requires` | string[] | 依赖的 artifact IDs，必须先存在 |

---

## 实战：创建自定义工作流

### 场景：快速迭代工作流

假设你的团队追求极致速度，只需要**提案 → 任务**两个阶段：

### Step 1: 创建 Schema 目录结构

```bash
mkdir -p openspec/schemas/rapid/templates
```

### Step 2: 编写 schema.yaml

```yaml
# openspec/schemas/rapid/schema.yaml
name: rapid
version: 1
description: 快速迭代工作流，跳过详细规格和设计阶段

artifacts:
  - id: proposal
    generates: proposal.md
    description: 快速提案
    template: proposal.md
    instruction: |
      创建一个简洁的提案，说明：
      1. 要解决的问题（2-3句话）
      2. 期望的结果
      3. 大致的实现思路
      不需要详细的技术细节。
    requires: []

  - id: tasks
    generates: tasks.md
    description: 实现任务清单
    template: tasks.md
    instruction: |
      基于提案创建实现任务：
      1. 每个任务应该小而具体
      2. 预估每个任务的时间
      3. 标记依赖关系
    requires:
      - proposal

apply:
  requires: [tasks]
  tracks: tasks.md
```

### Step 3: 创建 Templates

**proposal.md:**
```markdown
<!-- 快速提案模板 -->
## 问题

<!-- 要解决的问题，2-3句话描述 -->

## 期望结果

<!-- 完成后的预期效果 -->

## 实现思路

<!-- 大致的实现方向，不需要太详细 -->
```

**tasks.md:**
```markdown
<!-- 任务清单模板 -->
## 任务列表

<!-- 
格式：
- [ ] 任务描述 (预估时间) [依赖: 任务ID]
-->

## 依赖图

<!-- 如果有复杂依赖，可以用文本图表示 -->
```

### Step 4: 使用自定义工作流

```bash
# 方法1: 命令行指定
openspec new change my-feature --schema rapid

# 方法2: 设置为项目默认（在 config.yaml 中）
echo "schema: rapid" >> openspec/config.yaml
openspec new change my-feature  # 自动使用 rapid
```

---

## 高级用法

### 1. 添加 Review 步骤

如果你想在实现前增加代码审查环节：

```yaml
artifacts:
  # ... proposal, specs, design ...

  - id: review
    generates: review.md
    description: 实现前审查
    template: review.md
    instruction: |
      基于设计创建审查清单：
      1. 安全检查（SQL 注入、XSS 等）
      2. 性能考虑（大数据量、并发）
      3. 测试策略（单元测试、集成测试）
    requires:
      - design

  - id: tasks
    generates: tasks.md
    requires:
      - design
      - review  # 现在 tasks 需要 review 完成
```

### 2. 并行产物

某些产物可以并行创建：

```yaml
artifacts:
  - id: proposal
    requires: []

  - id: api-specs
    generates: specs/api.md
    requires:
      - proposal

  - id: ui-specs
    generates: specs/ui.md
    requires:
      - proposal
    # api-specs 和 ui-specs 可以并行创建
    # 它们都只需要 proposal

  - id: design
    requires:
      - api-specs
      - ui-specs
    # design 需要等待两者都完成
```

### 3. 使用 Glob 模式

一个 artifact 可以生成多个文件：

```yaml
artifacts:
  - id: specs
    generates: specs/**/*.md  # 生成 specs/ 目录下所有 .md 文件
    template: spec.md
    requires:
      - proposal
```

---

## 最佳实践

### 1. 从 Fork 开始

不要从零创建，先 fork 现有的：

```bash
# 复制 spec-driven，然后修改
openspec schema fork spec-driven my-workflow
```

### 2. 保持简单

刚开始时，artifact 不要超过 4-5 个。可以随着团队成熟逐步增加。

### 3. 验证 Schema

使用前务必验证：

```bash
openspec schema validate my-workflow
```

### 4. 版本控制

Schemas 应该和代码一起版本控制：

```bash
git add openspec/schemas/
git commit -m "添加自定义 rapid 工作流"
```

### 5. 文档化

在 `openspec/config.yaml` 或 README 中说明：

```yaml
# 项目使用 rapid 工作流，适合快速迭代
# 相比标准流程，跳过了详细的 specs 和 design 阶段
schema: rapid
```

---

## 常见问题

### Q: 自定义 Schema 和项目配置有什么区别？

- **项目配置** (`config.yaml`): 调整现有 Schema 的行为（设置默认、添加规则、注入上下文）
- **自定义 Schema**: 定义全新的产物和依赖关系，改变工作流结构

### Q: 可以组合多个 Schemas 吗？

不能直接组合，但可以通过 Fork 现有 Schema 并修改来实现类似效果。

### Q: 如何调试 Schema 问题？

```bash
# 查看 Schema 解析位置
openspec schema which my-workflow

# 列出所有可用 Schemas
openspec schema which --all

# 验证 Schema 语法
openspec schema validate my-workflow
```

### Q: 团队成员需要安装什么？

只需要安装 OpenSpec CLI：

```bash
npm install -g @fission-ai/openspec
```

Schemas 是随代码仓库分发的，团队成员自动获得相同的配置。

---

## 参考资源

- [OpenSpec 官方文档](https://docs.openspec.dev)
- [Customization Guide](./docs/customization.md)
- [Workflows Guide](./docs/workflows.md)

---

*文档版本: 1.0*
*最后更新: 2026-02-09*
