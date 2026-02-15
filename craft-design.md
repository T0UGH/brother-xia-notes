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

*设计完成，等待实现*
