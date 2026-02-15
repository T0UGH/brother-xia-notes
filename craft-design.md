# Craft 设计文档

> 交互式工作流生成器 —— 让技术团队通过对话定制专属工作流

---

## 1. 核心定位

### 1.1 一句话描述
**Craft** 是一个 AI 驱动的交互式工具，技术团队通过与 Agent 对话，为自己的团队定制专属的工作流（Spec Workflow），生成可直接在 Claude Code / OpenCode / Codex 中使用的 Skill 包。

### 1.2 双角色设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      Craft                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │   Creator        │          │   User           │            │
│  │   (创建者)        │          │   (使用者)        │            │
│  │                  │          │                  │            │
│  │  技术负责人/TL    │          │  团队开发者        │            │
│  │                  │          │                  │            │
│  │  职责：            │          │  职责：            │            │
│  │  - 定义团队工作流   │          │  - 使用定制好的    │            │
│  │  - 设计步骤和产物   │          │    工作流创建规格   │            │
│  │  - 生成 Skill 包   │          │  - 按步骤生成文档   │            │
│  │                  │          │                  │            │
│  │  使用命令：         │          │  使用命令：         │            │
│  │  craft      │          │  ff new            │            │
│  │    create          │          │  ff continue       │            │
│  │                  │          │  ff status         │            │
│  └──────────────────┘          └──────────────────┘            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    产物：Skill 包                         │   │
│  │              (Claude Code / OpenCode / Codex 可用)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 核心原则

| 原则 | 说明 |
|------|------|
| **对话优先** | 通过问答式交互，而非直接编辑配置文件 |
| **纯文本** | 产物是 YAML + Markdown，无图形界面 |
| **线性简单** | Level 1 复杂度，纯线性流程，足够解决 80% 场景 |
| **IDE 原生** | 产物是 Skill 包，直接嵌入 Claude Code / OpenCode / Codex |
| **团队复用** | 创建一次，整个团队共享使用 |

---

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Craft                            │
│                     (交互式工作流生成器)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    CLI 交互层                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│  │  │ 对话引擎      │  │ 问答解析器    │  │ 确认/选择    │       │ │
│  │  │ (Inquirer)   │  │ (Validation) │  │ (Confirm)    │       │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   核心引擎层                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│  │  │ 工作流定义   │  │ 步骤编排器   │  │ 依赖解析器   │       │ │
│  │  │ (Parser)     │  │ (Orchestrator)│ │ (Resolver)   │       │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │ │
│  │  ┌──────────────┐  ┌──────────────┐                        │ │
│  │  │ 变量管理器   │  │ 模板渲染器   │                        │ │
│  │  │ (Variables)  │  │ (Renderer)   │                        │ │
│  │  └──────────────┘  └──────────────┘                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   产物生成层                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│  │  │ Skill 打包器 │  │ YAML 生成器   │  │ 模板生成器   │       │ │
│  │  │ (Packager)   │  │ (YAML Gen)   │  │ (Template)   │       │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │ │
│  │  ┌──────────────┐                                          │ │
│  │  │ README 生成器 │                                          │ │
│  │  │ (Docs Gen)   │                                          │ │
│  │  └──────────────┘                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据模型

```typescript
// ============================================================================
// 核心数据模型
// ============================================================================

// 工作流定义（产物，供 ff 使用）
interface Workflow {
  name: string;           // 工作流名称，如 "feature-dev"
  description: string;      // 描述
  version: string;          // 语义化版本
  steps: WorkflowStep[];   // 步骤列表
  variables: WorkflowVariable[]; // 变量定义
}

// 工作流步骤（线性顺序执行）
interface WorkflowStep {
  id: string;             // 唯一标识，如 "prd"
  name: string;           // 显示名称，如 "产品需求文档"
  description?: string;   // 描述
  template: string;       // 模板文件名，如 "prd.md"
  output: string;         // 输出文件名，如 "01-prd.md"
  prompt: string;         // AI 生成提示词
  depends_on?: string[];  // 依赖的步骤 ID（线性简单依赖）
}

// 工作流变量（实例化时收集）
interface WorkflowVariable {
  name: string;           // 变量名，如 "featureName"
  type: 'string' | 'select' | 'boolean' | 'number';
  required: boolean;      // 是否必填
  prompt: string;         // 向用户询问时的提示
  options?: string[];     // type=select 时的选项
  default?: any;          // 默认值
}

// ============================================================================
// Craft 内部模型（对话过程）
// ============================================================================

// 对话上下文
interface CreatorContext {
  phase: 'init' | 'steps' | 'variables' | 'review' | 'complete';
  workflowName: string;
  workflowDescription: string;
  steps: Partial<WorkflowStep>[];
  variables: Partial<WorkflowVariable>[];
  currentStep: number;
}

// 对话消息
interface ConversationMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// Skill 包结构（产物，供 IDE 使用）
// ============================================================================

/*
my-workflow-skill/
├── SKILL.md                 # 技能定义（Claude Code / OpenCode 读取）
├── workflow.yaml            # 工作流定义（供 ff 使用）
├── templates/               # 文档模板
│   ├── prd.md
│   ├── tech-spec.md
│   └── tasks.md
└── README.md                # 使用说明
*/

// SKILL.md 结构示例
interface SkillDefinition {
  name: string;
  description: string;
  triggers: string[];      // 触发关键词
  workflow: string;        // 关联的 workflow.yaml 路径
}
```

### 2.3 交互流程

```
┌─────────────────────────────────────────────────────────────────┐
│              Craft 交互流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐                                                    │
│  │  开始    │                                                    │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌───────────────────┐                                             │
│  │ Phase 1: 初始化    │                                             │
│  │ ─────────────────  │                                             │
│  │ Agent: 你好！我是  │                                             │
│  │ Craft...   │                                             │
│  │                   │                                             │
│  │ Q: 这个工作流用于 │                                             │
│  │    什么场景？      │                                             │
│  │    (如：功能开发、 │                                             │
│  │     API设计...)   │                                             │
│  │                   │                                             │
│  │ A: [用户输入]     │                                             │
│  │                   │                                             │
│  │ Q: 工作流名称？   │                                             │
│  │    (如：feature-  │                                             │
│  │     dev)          │                                             │
│  │                   │                                             │
│  │ A: [用户输入]     │                                             │
│  └────────┬──────────┘                                             │
│           ▼                                                      │
│  ┌───────────────────┐                                             │
│  │ Phase 2: 定义步骤  │                                             │
│  │ ─────────────────  │                                             │
│  │ Agent: 好的，      │                                             │
│  │ [工作流名] 包含   │                                             │
│  │ 哪些步骤？        │                                             │
│  │                   │                                             │
│  │ 例如：           │                                             │
│  │ 1. 产品需求文档   │                                             │
│  │ 2. 技术方案      │                                             │
│  │ 3. 任务拆分      │                                             │
│  │                   │                                             │
│  │ A: 3个步骤       │                                             │
│  │                   │                                             │
│  │ Q: 第1步的名称   │                                             │
│  │    和ID？        │                                             │
│  │    (如：产品需求 │                                             │
│  │     文档/prd)    │                                             │
│  │                   │                                             │
│  │ A: PRD/prd      │                                             │
│  │                   │                                             │
│  │ Q: 这一步的      │                                             │
│  │    AI提示词是？  │                                             │
│  │    (告诉AI如何  │                                             │
│  │     生成这一步   │                                             │
│  │     的产物)     │                                             │
│  │                   │                                             │
│  │ A: [多行输入    │                                             │
│  │     提示词]      │                                             │
│  │                   │                                             │
│  │ [继续第2、3步...]│                                             │
│  │                   │                                             │
│  │ Q: 步骤之间     │                                             │
│  │    有依赖关系吗？│                                             │
│  │    (如：步骤2   │                                             │
│  │     需要步骤1   │                                             │
│  │     的产物)      │                                             │
│  │                   │                                             │
│  │ A: 是的，       │                                             │
│  │    第2步依赖第1步│                                             │
│  │    第3步依赖第2步│                                             │
│  │                   │                                             │
│  │ [自动设置       │                                             │
│  │  depends_on]     │                                             │
│  └──────────────────┘                                             │
│           ▼                                                      │
│  ┌───────────────────┐                                             │
│  │ Phase 3: 定义变量   │                                             │
│  │ ─────────────────  │                                             │
│  │ Agent: 创建       │                                             │
│  │ 工作流实例时，      │                                             │
│  │ 需要收集           │                                             │
│  │ 哪些信息？         │                                             │
│  │                   │                                             │
│  │ 例如：            │                                             │
│  │ - 功能名称        │                                             │
│  │ - 优先级          │                                             │
│  │ - 负责人          │                                             │
│  │                   │                                             │
│  │ A: 3个变量        │                                             │
│  │                   │                                             │
│  │ Q: 第1个变量      │                                             │
│  │    的名称？       │                                             │
│  │    (如：          │                                             │
│  │     featureName)  │                                             │
│  │                   │                                             │
│  │ A: featureName    │                                             │
│  │                   │                                             │
│  │ Q: 类型？         │                                             │
│  │    (string/       │                                             │
│  │     select/       │                                             │
│  │     boolean/      │                                             │
│  │     number)       │                                             │
│  │                   │                                             │
│  │ A: string         │                                             │
│  │                   │                                             │
│  │ Q: 提示语？       │                                             │
│  │    (向用户        │                                             │
│  │     询问时显示)   │                                             │
│  │                   │                                             │
│  │ A: 请输入功能名称 │                                             │
│  │                   │                                             │
│  │ Q: 是否必填？     │                                             │
│  │                   │                                             │
│  │ A: 是             │                                             │
│  │                   │                                             │
│  │ [继续第2、3个    │                                             │
│  │  变量...]         │                                             │
│  └──────────────────┘                                             │
│           ▼                                                      │
│  ┌───────────────────┐                                             │
│  │ Phase 4: 确认与生成 │                                             │
│  │ ─────────────────  │                                             │
│  │ Agent: 这是        │                                             │
│  │ 工作流的概览：      │                                             │
│  │                   │                                             │
│  │ [显示完整配置     │                                             │
│  │  摘要]              │                                             │
│  │                   │                                             │
│  │ 工作流名称：xxx   │                                             │
│  │ 步骤数：3         │                                             │
│  │ 变量数：3         │                                             │
│  │                   │                                             │
│  │ [显示步骤列表    │                                             │
│  │  和变量列表]       │                                             │
│  │                   │                                             │
│  │ Q: 确认生成？     │                                             │
│  │    (是/否/       │                                             │
│  │     修改某部分)   │                                             │
│  │                   │                                             │
│  │ A: 是             │                                             │
│  │                   │                                             │
│  │ [生成 Skill 包   │                                             │
│  │  并保存]           │                                             │
│  │                   │                                             │
│  │ ✅ 工作流已生成！ │                                             │
│  │                   │                                             │
│  │ 📁 位置：         │                                             │
│  │    .spec-flows/  │                                             │
│  │    my-workflow/  │                                             │
│  │                  │                                             │
│  │ 📦 产物：         │                                             │
│  │    - SKILL.md    │                                             │
│  │    - workflow.yaml│                                            │
│  │    - templates/  │                                             │
│  │                  │                                             │
│  │ 💡 使用方法：      │                                             │
│  │    1. 将 Skill   │                                             │
│  │       包复制到    │                                             │
│  │       Claude Code│                                             │
│  │       的 skills  │                                             │
│  │       目录       │                                             │
│  │    2. 使用       │                                             │
│  │       "@my-     │                                             │
│  │       workflow"  │                                             │
│  │       触发       │                                             │
│  └──────────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 产物格式（Skill 包）

Craft 的最终产物是一个 **Skill 包**，可直接被 Claude Code / OpenCode / Codex 加载使用。

### 3.1 Skill 包目录结构

```
my-workflow-skill/
├── SKILL.md                    # 技能定义（入口）
├── workflow.yaml               # 工作流定义（供 ff 使用）
├── templates/                  # 文档模板目录
│   ├── prd.md
│   ├── tech-spec.md
│   └── tasks.md
├── scripts/                    # 可选：辅助脚本
│   └── utils.js
└── README.md                   # 使用说明
```

### 3.2 SKILL.md 模板

```markdown
---
name: {{workflowName}}
description: |
  {{workflowDescription}}
  
  使用此技能创建结构化的 {{workflowName}} 规格文档。
  
  触发方式：输入 "@{{workflowName}}" 或 "开始 {{workflowName}}"
---

# {{workflowName}} 工作流

{{workflowDescription}}

## 使用方式

1. 输入 `@{{workflowName}}` 触发工作流
2. 按提示回答变量问题
3. 按步骤生成文档
4. 使用 `ff continue` 继续下一步

## 工作流步骤

{{#steps}}
### {{number}}. {{name}} ({{id}})

- **产物**：{{output}}
- **描述**：{{description}}
- **依赖**：{{depends_on}}

**AI 提示词**：
```
{{prompt}}
```

{{/steps}}

## 变量定义

{{#variables}}
- `{{name}}` ({{type}}){{#required}} *必填*{{/required}}
  - 提示：{{prompt}}
  {{#options}}
  - 选项：{{.}}
  {{/options}}

{{/variables}}

## 文件结构

```
.ff/
└── workflows/
    └── {{workflowName}}/
        ├── workflow.yaml
        └── templates/
            {{#steps}}
            ├── {{id}}.md
            {{/steps}}
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `ff new` | 创建新规格实例 |
| `ff continue` | 继续下一步 |
| `ff status` | 查看当前状态 |
| `ff list` | 列出所有规格 |

---

*由 Craft 自动生成*
```

### 3.3 workflow.yaml 模板

```yaml
name: {{workflowName}}
description: {{workflowDescription}}
version: 1.0.0

# 步骤定义（线性顺序执行）
steps:
{{#steps}}
  - id: {{id}}
    name: {{name}}
    description: {{description}}
    template: {{id}}.md
    output: {{output}}
    prompt: |
      {{prompt}}
    {{#depends_on}}
    depends_on:
      {{#depends_on}}
      - {{.}}
      {{/depends_on}}
    {{/depends_on}}
{{/steps}}

# 变量定义
variables:
{{#variables}}
  - name: {{name}}
    type: {{type}}
    required: {{required}}
    prompt: {{prompt}}
    {{#options}}
    options:
      {{#options}}
      - {{.}}
      {{/options}}
    {{/options}}
    {{#default}}
    default: {{default}}
    {{/default}}
{{/variables}}
```

---

## 4. 命令行界面

### 4.1 craft 命令（创建者使用）

```bash
# 交互式创建工作流
craft create

# 基于模板创建工作流
craft create --template feature-dev

# 列出可用模板
craft templates

# 验证工作流定义
craft validate ./my-workflow/

# 编辑现有工作流
craft edit ./my-workflow/
```

### 4.2 ff 命令（使用者使用）

```bash
# 查看帮助
ff --help

# 创建新规格实例（交互式选择工作流）
ff new

# 使用特定工作流创建规格
ff new --workflow feature-dev

# 继续执行工作流的下一步
ff continue

# 查看当前规格状态
ff status

# 列出所有规格实例
ff list

# 查看规格详情
ff show <spec-name>
```

---

## 5. 技术实现

### 5.1 技术栈

| 组件 | 技术 |
|------|------|
| 运行时 | Node.js 18+ |
| 语言 | TypeScript |
| CLI 框架 | Commander.js |
| 交互式提示 | Inquirer.js |
| 模板引擎 | Handlebars |
| YAML 处理 | js-yaml |
| 文件系统 | fs-extra |

### 5.2 目录结构

```
craft/
├── src/
│   ├── cli/
│   │   ├── commands/
│   │   │   ├── create.ts       # craft create
│   │   │   ├── validate.ts     # craft validate
│   │   │   └── edit.ts         # craft edit
│   │   ├── prompts/
│   │   │   ├── workflow.ts     # 工作流信息收集
│   │   │   ├── steps.ts        # 步骤定义收集
│   │   │   └── variables.ts    # 变量定义收集
│   │   └── index.ts            # CLI 入口
│   ├── core/
│   │   ├── WorkflowBuilder.ts  # 工作流构建器
│   │   ├── TemplateEngine.ts   # 模板引擎
│   │   ├── SkillPackager.ts    # Skill 打包器
│   │   └── validators/
│   │       └── WorkflowValidator.ts
│   ├── types/
│   │   └── index.ts            # 类型定义
│   └── utils/
│       ├── file.ts
│       └── yaml.ts
├── templates/
│   └── builtin/                # 内置模板
│       ├── feature-dev/
│       ├── api-design/
│       └── bug-fix/
├── bin/
│   └── craft.js         # 可执行文件
├── package.json
├── tsconfig.json
└── README.md
```

---

## 6. 使用场景示例

### 场景 1：创建功能开发工作流

```bash
$ craft create

🚀 Craft - 交互式工作流生成器

📋 Phase 1: 基本信息

Q: 这个工作流用于什么场景？
   (如：功能开发、API设计、Bug修复...)
A: 功能开发

Q: 工作流名称？(如：feature-dev)
A: feature-dev

Q: 工作流描述？
A: 标准功能开发流程，从 PRD 到任务拆分

🔧 Phase 2: 定义工作流步骤

提示：每个步骤对应一个产物（如文档、代码等）

Q: 这个工作流包含多少个步骤？
A: 3

--- 步骤 1 ---
Q: 步骤 ID？(如：prd)
A: prd

Q: 步骤名称？
A: 产品需求文档

Q: 步骤描述？
A: 撰写产品需求文档，明确功能目标和验收标准

Q: 输出文件名？(如：01-prd.md)
A: 01-prd.md

Q: AI 提示词？（告诉 AI 如何生成这一步的产物）
A:
基于功能名称和描述，撰写产品需求文档（PRD）。

必须包含：
1. 背景和目标
2. 用户故事
3. 功能需求（Given/When/Then 格式）
4. 验收标准
5. 非功能需求（性能、安全等）

功能名称：{{featureName}}
功能描述：{{description}}

[继续步骤 2、3...]

--- 步骤 2: 技术方案 / tech-spec ---
--- 步骤 3: 任务拆分 / tasks ---

Q: 步骤之间有依赖关系吗？
A: 是的

[自动设置 depends_on]
- tech-spec 依赖 prd
- tasks 依赖 tech-spec

📦 Phase 3: 定义变量

Q: 创建工作流实例时，需要收集哪些信息？
A: 2个

--- 变量 1 ---
Q: 变量名？(如：featureName)
A: featureName

Q: 类型？(string/select/boolean/number)
A: string

Q: 提示语？
A: 请输入功能名称

Q: 是否必填？
A: 是

[继续变量 2: priority (select) ...]

🔍 Phase 4: 确认与生成

Agent: 这是工作流的概览：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
工作流名称：feature-dev
描述：标准功能开发流程，从 PRD 到任务拆分

步骤：
  1. PRD (prd) → 01-prd.md
  2. 技术方案 (tech-spec) → 02-tech-spec.md
     依赖: prd
  3. 任务拆分 (tasks) → 03-tasks.md
     依赖: tech-spec

变量：
  - featureName (string) *必填*
  - priority (select) *必填*
    选项: P0, P1, P2, P3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: 确认生成？
A: 是

🚀 生成工作流...

✅ 工作流已生成！

📁 位置: .spec-flows/feature-dev/

📦 产物:
   - SKILL.md
   - workflow.yaml
   - templates/
     ├── prd.md
     ├── tech-spec.md
     └── tasks.md
   - README.md

💡 使用方法:
   1. 将 SKILL.md 和相关文件复制到
      Claude Code 的 .claude/skills/ 目录
   2. 在 Claude Code 中使用:
      @feature-dev 或 "开始功能开发"

   或使用 ff CLI:
   $ ff new --workflow feature-dev
```

### 场景 2：开发者使用定制好的工作流

```bash
$ ff new

🚀 Craft - 规格工作流 CLI

Q: 选择工作流：
   1. feature-dev (功能开发)
   2. api-design (API设计)
   3. bug-fix (Bug修复)
A: 1

📋 创建工作流实例

Q: 功能名称？
A: 用户登录功能

Q: 优先级？
   1. P0
   2. P1
   3. P2
   4. P3
A: 1

✅ 工作流实例已创建

📁 位置: .specs/user-login-feature/

当前步骤: 1/3 - PRD (产品需求文档)

💡 下一步:
   $ ff continue
   或
   $ ff status

---

$ ff continue

🔄 继续执行工作流

当前步骤: 1/3 - PRD (产品需求文档)

Agent: 我将基于以下信息生成产品需求文档：
- 功能名称: 用户登录功能
- 优先级: P0

正在生成 PRD...

✅ 步骤完成

📄 产物: .specs/user-login-feature/01-prd.md

📝 内容摘要:
   - 背景和目标
   - 用户故事
   - 功能需求
   - 验收标准

💡 下一步:
   $ ff continue

[继续执行步骤 2: 技术方案]
[继续执行步骤 3: 任务拆分]

---

$ ff status

📊 工作流实例状态

名称: user-login-feature
工作流: feature-dev

进度: 3/3 ✅ 已完成

步骤状态:
  ✅ 1. PRD (产品需求文档)
     📄 01-prd.md
  ✅ 2. 技术方案
     📄 02-tech-spec.md
  ✅ 3. 任务拆分
     📄 03-tasks.md

产物位置: .specs/user-login-feature/
```

---

## 7. 与 OpenSpec 的关系

| 维度 | OpenSpec | Craft |
|------|----------|--------------|
| **目标用户** | 终端开发者 | 技术负责人/TL |
| **使用方式** | 直接使用 | 先创建，再使用 |
| **产物** | 规格文档 | 可复用的工作流（Skill 包） |
| **定制方式** | 手写 YAML | 交互式对话生成 |
| **复杂度** | 需学习完整 Schema | 问答式引导，无学习成本 |
| **关系** | 底层引擎 | 上层生成器 |

**Craft 与 OpenSpec 的关系，类似于：**
- `create-react-app` 与 React
- `vue-cli` 与 Vue
- `skill-creator` 与 Skill 运行时

Craft 生成的 Skill 包，底层可以**兼容 OpenSpec 的规范**，或者直接使用 **ff CLI** 作为运行时。

---

## 8. 实现路线图

### Phase 1: MVP（2 周）
- [ ] 基础对话流程（4 个 Phase）
- [ ] Skill 包生成（SKILL.md + workflow.yaml）
- [ ] 内置 3 个模板（feature-dev, api-design, bug-fix）
- [ ] 基础 CLI（craft create）

### Phase 2: 可用（2 周）
- [ ] ff CLI 基础命令（new, continue, status）
- [ ] Claude Code 插件集成
- [ ] 模板编辑和保存
- [ ] 工作流验证

### Phase 3: 完善（2 周）
- [ ] OpenCode / Codex 支持
- [ ] 高级模板功能（条件、循环）
- [ ] 工作流共享机制
- [ ] 文档和示例

---

## 9. 下一步行动

基于以上设计，下一步可以：

1. **评审设计** — 确认上述设计满足需求
2. **细化数据模型** — 定义完整的 TypeScript 接口
3. **编写示例** — 用真实场景验证交互流程
4. **开始实现** — 从 MVP Phase 1 开始编码

---

*设计完成，等待反馈*
