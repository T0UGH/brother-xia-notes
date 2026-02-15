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
