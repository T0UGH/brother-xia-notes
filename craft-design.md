# Craft 设计文档

> 交互式工作流生成器 —— 让技术团队通过对话定制专属工作流

---

## 1. 核心定位

### 1.1 一句话描述
**Craft** 是一个 AI 驱动的交互式工具，技术团队通过与 Agent 对话，为自己的团队定制专属的工作流，生成可直接在 Claude Code / OpenCode / Codex 中使用的 Skill 包。

### 1.2 双角色设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         Craft                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │   Creator        │          │   User           │            │
│  │   (创建者)        │          │   (使用者)        │            │
│  │                  │          │                  │            │
│  │  技术负责人/TL    │          │  团队开发者        │            │
│  │                  │          │                  │            │
│  │  使用命令：         │          │  使用命令：         │            │
│  │  craft create      │          │  craft new         │            │
│  │                  │          │  craft next        │            │
│  │                  │          │  craft status      │            │
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

## 2. 命令设计

### 2.1 统一命令

```bash
# 核心命令（所有工作流通用）
craft new          # 创建新规格实例（交互式选择工作流）
craft next         # 继续执行下一步
craft status       # 查看当前状态
craft list         # 列出所有规格

# 创建者命令
craft create       # 交互式创建新工作流
craft validate     # 验证工作流配置
```

---

## 3. 用户使用流程

```bash
$ craft new
? 选择工作流: feature-dev
? 功能名称: 用户登录
? 优先级: P0

✅ 已创建: specs/user-login/
   当前步骤: 1/3 - PRD

$ craft next
🔄 执行 PRD 步骤...
✅ 完成: specs/user-login/01-prd.md

$ craft next
🔄 执行 技术方案 步骤...
```

---

## 4. 创建者使用流程

```bash
$ craft create

🚀 Craft - 交互式工作流生成器

📋 Phase 1: 基本信息
Q: 工作流名称？ A: feature-dev
Q: 描述？ A: 标准功能开发流程

🔧 Phase 2: 定义步骤
Q: 步骤数？ A: 3
  - 步骤1: PRD → 01-prd.md
  - 步骤2: 技术方案 → 02-tech-spec.md (依赖PRD)
  - 步骤3: 任务拆分 → 03-tasks.md (依赖技术方案)

📦 Phase 3: 定义变量
  - featureName (string, 必填)
  - priority (select: P0/P1/P2/P3, 必填)

🔍 Phase 4: 确认生成
[显示完整配置摘要]
Q: 确认生成？ A: 是

✅ 工作流已生成！
📁 位置: .craft/workflows/feature-dev/
📦 产物: SKILL.md, workflow.yaml, templates/, README.md
```

---

## 5. Skill 包结构

```
feature-dev/
├── SKILL.md              # 技能定义（Claude Code 读取）
├── workflow.yaml         # 工作流定义
├── templates/            # 文档模板
│   ├── prd.md
│   ├── tech-spec.md
│   └── tasks.md
└── README.md             # 使用说明
```

---

## 5. NPM 包设计

为了实现 Craft 的功能，我们需要发布两个 npm 包：

### 5.1 包列表

| 包名 | 作用 | 目标用户 | 安装方式 |
|------|------|----------|----------|
| `@craft/cli` | 核心 CLI 工具，包含 `craft new/next/status` 等所有命令 | 开发者（使用者） | `npm i -g @craft/cli` 或 `npx @craft/cli` |
| `@craft/create` | 交互式创建工作流的向导 | 技术负责人（创建者） | `npx @craft/create` |

### 5.2 命令对应关系

```bash
# 创建者（技术负责人）
npx @craft/create
# 或全局安装
npm i -g @craft/create
craft create    # 交互式创建工作流

# 使用者（开发者）
npx @craft/cli new
# 或全局安装
npm i -g @craft/cli
craft new       # 使用工作流创建规格
craft next      # 继续下一步
craft status    # 查看状态
```

### 5.3 包结构

#### `@craft/cli` 结构

```
@craft/cli/
├── bin/
│   └── craft.js            # 入口脚本
├── src/
│   ├── index.ts            # 主入口
│   ├── commands/           # 子命令实现
│   │   ├── new.ts
│   │   ├── next.ts
│   │   └── status.ts
│   ├── core/               # 核心引擎
│   │   ├── WorkflowRunner.ts
│   │   ├── StepExecutor.ts
│   │   └── VariableResolver.ts
│   └── utils/
├── package.json
└── README.md
```

#### `@craft/create` 结构

```
@craft/create/
├── bin/
│   └── craft-create.js     # 入口脚本
├── src/
│   ├── index.ts             # 主入口
│   ├── prompts/             # 交互式问答
│   │   ├── workflow.ts
│   │   ├── steps.ts
│   │   └── variables.ts
│   ├── generators/          # 文件生成器
│   │   ├── WorkflowGenerator.ts
│   │   ├── TemplateGenerator.ts
│   │   └── SkillPackager.ts
│   └── templates/           # 内置模板
│       ├── feature-dev/
│       ├── api-design/
│       └── bug-fix/
├── package.json
└── README.md
```

### 5.4 发布计划

| 阶段 | 包 | 版本 | 内容 |
|------|-----|------|------|
| Phase 1 | `@craft/create` | 0.1.0 | MVP：支持基础交互式创建工作流 |
| Phase 2 | `@craft/cli` | 0.1.0 | MVP：支持 `craft new/next/status` |
| Phase 3 | 两者 | 0.2.0 | 完善模板系统、验证机制、错误处理 |
| Phase 4 | 两者 | 1.0.0 | 正式版，完整文档和示例 |

---

## 6. 实现路线图

### Phase 1: MVP（2 周）
- [ ] 搭建 `@craft/create` 基础结构
- [ ] 实现交互式问答流程（4 个 Phase）
- [ ] 实现 Skill 包生成器
- [ ] 内置 3 个模板（feature-dev, api-design, bug-fix）

### Phase 2: CLI 工具（2 周）
- [ ] 搭建 `@craft/cli` 基础结构
- [ ] 实现 `craft new` 命令
- [ ] 实现 `craft next` 命令
- [ ] 实现 `craft status` 命令

### Phase 3: 完善（2 周）
- [ ] 完善模板系统
- [ ] 添加验证机制
- [ ] 改进错误处理
- [ ] 编写完整文档和示例

---

*设计完成，等待实现*

## 7. 高级功能设计

### 7.1 文档分章节生成

支持在 template 中定义每次 craft next 生成文档的特定章节，而不是一次性生成整个文档。

**template 示例：**

```yaml
# prd-template.yaml
chapters:
  - id: background
    title: 背景与目标
    description: 说明为什么要做这个功能
  - id: user-stories
    title: 用户故事
    description: 以用户视角描述需求
  - id: requirements
    title: 功能需求
    description: 详细的功能点描述
  - id: acceptance-criteria
    title: 验收标准
    description: 如何验证功能完成

# 步骤配置中指定每次生成哪些章节
steps:
  - id: prd
    name: 产品需求文档
    template: prd-template.yaml
    output: 01-prd.md
    chapterGeneration:
      - step: 1
        chapters: [background, user-stories]
      - step: 2
        chapters: [requirements, acceptance-criteria]
```

### 7.2 强制加载知识性 Skills

支持在文档写作前或特定章节写作前，自动加载指定的知识性 Skills，为 AI 提供领域知识支持。

**配置示例：**

```yaml
# workflow.yaml
steps:
  - id: tech-spec
    name: 技术方案文档
    template: tech-spec.md
    output: 02-tech-spec.md
    requiredSkills:
      - id: company-tech-stack
        name: 公司技术栈规范
        description: 包含公司标准技术选型、框架版本、编码规范
      - id: security-guidelines
        name: 安全开发规范
        description: 包含安全编码要求、常见漏洞防护
    chapterSkills:
      - chapterId: architecture
        requiredSkills:
          - id: microservices-patterns
            name: 微服务设计模式
```

### 7.3 SubAgent 支持

支持在任何步骤中启动 SubAgent 来并行处理任务，或处理需要隔离上下文的复杂任务。

**配置示例：**

```yaml
# workflow.yaml
steps:
  - id: security-review
    name: 安全评审
    template: security-review.md
    subAgents:
      - id: owasp-check
        name: OWASP 漏洞扫描
        prompt: |
          作为安全专家，请审查以下代码/设计是否存在 OWASP Top 10 漏洞：
          {{context.codeOrDesign}}
          输出格式：
          - 问题行号: 问题描述
      - id: data-privacy-check
        name: 数据隐私合规检查
        prompt: |
          作为隐私合规专家，请审查以下设计是否符合 GDPR/个人信息保护法：
          {{context.dataHandling}}
          输出：
          1. 隐私风险点
          2. 合规建议
      - id: security-report
        name: 安全评审报告生成
        dependsOn: [owasp-check, data-privacy-check]
        prompt: |
          基于以下检查结果生成完整的安全评审报告：
          ## OWASP 漏洞扫描结果
          {{subAgents.owasp-check.output}}
          ## 数据隐私合规检查结果
          {{subAgents.data-privacy-check.output}}
          输出：
          1. 执行摘要
          2. 详细发现
          3. 优先级建议
```

### 7.4 上下文压缩建议

当检测到上下文过长时，系统应主动建议用户进行上下文压缩或启动新的 SubAgent。

**触发条件：**
- Token 数超过阈值（如 8000）
- 对话轮次过多（如 20 轮以上）
- 单次输出内容过长

**建议策略：**

```typescript
interface CompressionSuggestion {
  type: 'compress' | 'subagent' | 'summarize';
  reason: string;
  action: string;
}

class ContextManager {
  private tokenThreshold = 8000;
  private roundThreshold = 20;
  
  checkContext(context: ExecutionContext): CompressionSuggestion | null {
    const tokenCount = this.estimateTokens(context);
    const roundCount = context.conversationRounds;
    
    if (tokenCount > this.tokenThreshold) {
      return {
        type: 'compress',
        reason: `当前上下文约 ${tokenCount} tokens，接近模型上限`,
        action: '建议压缩历史对话，只保留关键决策和当前状态'
      };
    }
    
    if (roundCount > this.roundThreshold) {
      return {
        type: 'subagent',
        reason: `对话已进行 ${roundCount} 轮，上下文累积过多`,
        action: '建议启动 SubAgent 处理当前任务，主 Agent 只关注结果'
      };
    }
    
    return null;
  }
}
```

**用户界面示例：**

```bash
$ craft next

⚠️  上下文提示

当前对话已进行 25 轮，上下文累积较多。
建议启动 SubAgent 来处理当前任务，以提高效率。

选项：
  1. 启动 SubAgent（推荐）
  2. 继续当前上下文
  3. 压缩上下文后继续

请选择: 1

🚀 启动 SubAgent 处理当前任务...
```

