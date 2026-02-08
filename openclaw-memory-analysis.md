# OpenClaw 长久记忆机制深度分析

> 与 Claude Code、Codex 等编程 Agent 的记忆系统对比

---

## 一、核心结论（TL;DR）

| 维度 | OpenClaw | Claude Code | Codex | Superpowers |
|-----|----------|-------------|-------|-------------|
| **记忆哲学** | 文件即真相 + 向量索引 | 会话归档 + 工作区文件 | Prompt 上下文 + 文件系统 | 方法论框架，不管理记忆 |
| **存储层** | Markdown + SQLite + 可选 QMD | Git + 工作区文件 | 无持久化，依赖外部 | 不涉及 |
| **搜索能力** | 向量 + BM25 混合搜索 | 无内置搜索，依赖 grep | 无 | 无 |
| **会话记忆** | 自动 flush + 可选索引 | 手动 /new 归档 | 无 | 无 |
| **架构复杂度** | 高（模块化、可扩展） | 中（内置技能） | 低（简单编程助手） | 中（方法论框架） |

**关键洞察：**

OpenClaw 的记忆系统本质上是一个**本地优先的语义知识库**，而 Claude Code/Codex 的记忆更多是**会话状态的临时延续**。OpenClaw 把"记忆"当作一等公民来设计，而其他工具把记忆当作实现细节的副产品。

---

## 二、OpenClaw 记忆系统架构详解

### 2.1 核心设计哲学：文件即真相 (Files are the Source of Truth)

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw Memory                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Markdown Files (Source of Truth)                  │
│  ├── MEMORY.md           ← 长期精选记忆（人工维护）            │
│  └── memory/YYYY-MM-DD.md ← 每日日志（自动/人工写入）        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Index (Performance Layer)                         │
│  ├── SQLite (~/.openclaw/memory/<agentId>.sqlite)           │
│  │   ├── 向量索引 (embeddings)                               │
│  │   └── BM25 全文索引 (FTS5)                               │
│  └── QMD (可选)     ← 高级混合搜索后端                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Tools (Interface)                                 │
│  ├── memory_search  ← 语义搜索（返回片段+路径+行号）          │
│  └── memory_get    ← 精确读取（按路径+可选行范围）            │
└─────────────────────────────────────────────────────────────┘
```

**关键设计决策：**

1. **Markdown 作为通用格式**：人类可读、版本控制友好、工具生态丰富
2. **分层架构**：文件层（真相）→ 索引层（性能）→ 工具层（接口）
3. **可选的 QMD 后端**：对于高级用户，可以切换到更强大的混合搜索（BM25 + 向量 + Rerank）

### 2.2 记忆生命周期管理

#### 阶段 1：写入（Write）

```
触发条件：
├── 显式：用户说"记住这个" → 立即写入 memory/YYYY-MM-DD.md
├── 自动：Session 接近 compaction 时触发 memory flush
│   └── 系统发送提示："Session nearing compaction. Store durable memories now."
│   └── 模型决定写入内容，回复 NO_REPLY（用户无感知）
└── 手动：Agent 随时调用工具写入

写入内容层级：
├── 事实/决策 → MEMORY.md（长期）
└── 日常/上下文 → memory/YYYY-MM-DD.md（短期）
```

#### 阶段 2：索引（Index）

```
索引策略：
├── 文件监听：watch MEMORY.md + memory/ 目录
├── 防抖：1.5 秒 debounce（避免频繁写入触发重索引）
├── 异步：索引更新在后台线程进行，不阻塞会话
├── 触发时机：
│   ├── 会话启动时
│   ├── 搜索时（如果索引 dirty）
│   └── 定期（可配置 interval）
└── 增量：只处理变更的 chunks

分块策略：
├── 目标大小：~400 tokens per chunk
├── 重叠：80 tokens overlap（保证语义连续性）
└── 元数据：保留文件路径、行号范围
```

#### 阶段 3：检索（Retrieve）

```
搜索流程：
1. 用户/Agent 调用 memory_search(query)
2. 系统检查索引状态（如 dirty 则先更新）
3. 执行混合搜索（Hybrid Search）：
   ├── 向量搜索：topK by cosine similarity
   ├── BM25 搜索：topK by keyword relevance
   └── 融合：加权合并（默认 vectorWeight=0.7, textWeight=0.3）
4. 去重 + 重排序
5. 返回片段（snippet）：
   ├── 内容（~700 chars max）
   ├── 源文件路径
   ├── 行号范围
   ├── 相似度分数
   └── 使用的模型/Provider

工具配合：
├── memory_search：返回候选片段（不包含完整内容）
└── memory_get：按精确路径读取完整文件（或指定行范围）
```

### 2.3 与 Claude Code、Codex 的对比维度

#### 维度 1：记忆持久化模型

| 特性 | OpenClaw | Claude Code | Codex |
|-----|----------|-------------|-------|
| **持久化层** | 本地 Markdown + SQLite | Git + 工作区文件 | 无内置持久化 |
| **跨会话记忆** | ✅ 自动索引和搜索 | ⚠️ 依赖用户手动管理文件 | ❌ 每次新会话 |
| **语义搜索** | ✅ 向量 + BM25 混合 | ❌ 无 | ❌ 无 |
| **记忆粒度** | 段落级 (chunks) | 文件级 | 无 |

**关键差异分析：**

- **OpenClaw**：把记忆当作核心功能设计，提供了完整的"写入→索引→检索"闭环
- **Claude Code**：更轻量，依赖用户通过 `/new` 命令手动归档会话，没有内置的语义检索能力
- **Codex**：纯编程助手，记忆完全依赖外部系统（如文件系统），本身不提供记忆管理

#### 维度 2：会话管理与上下文延续

| 特性 | OpenClaw | Claude Code | Codex |
|-----|----------|-------------|-------|
| **Compaction 策略** | 自动 + 可配置阈值 | 固定策略 | 无 |
| **预 compaction flush** | ✅ 自动触发记忆写入 | ❌ 无 | ❌ 无 |
| **会话归档** | ✅ 可选索引会话日志 | ✅ `/new` 命令 | ❌ 无 |
| **子 Agent 通信** | ✅ sessions_send/spawn | ⚠️ 有限支持 | ❌ 无 |

**OpenClaw 的独特优势：**

1. **自动记忆 flush**：在 compaction 前自动提醒 Agent 写入重要记忆，避免上下文丢失
2. **子 Agent 系统**：支持 sessions_spawn 创建独立子会话，子 Agent 完成后结果返回父会话
3. **会话日志索引**：可选将会话记录也纳入向量索引，实现"对话历史"的语义搜索

#### 维度 3：架构可扩展性

| 特性 | OpenClaw | Claude Code | Codex |
|-----|----------|-------------|-------|
| **插件系统** | ✅ 完整插件生态 | ❌ 内置技能 | ❌ 无 |
| **记忆后端切换** | ✅ SQLite / QMD | ❌ 固定 | ❌ 无 |
| **嵌入模型选择** | ✅ OpenAI / Gemini / Local | ❌ 固定 | ❌ 无 |
| **多 Agent 支持** | ✅ 完整 Agent 管理 | ⚠️ 有限 | ❌ 单会话 |

---

## 三、深层分析：为什么 OpenClaw 的记忆设计更先进？

### 3.1 "文件即真相"的哲学优势

OpenClaw 选择 Markdown 文件作为记忆的"唯一真相来源"，这个设计决策有深远影响：

**1. 可审计性 (Auditability)**
- 人类可以直接阅读记忆文件
- 可以用 Git 版本控制记忆的变更历史
- 随时可以人工修正或补充记忆

**2. 工具互操作性 (Interoperability)**
- Markdown 是通用格式，可以被任何工具处理
- 可以用 Obsidian、VS Code 等编辑器查看
- 可以用标准 Unix 工具（grep、awk）处理

**3. 长期可维护性 (Longevity)**
- 不依赖特定数据库格式
- 即使 OpenClaw 停止维护，记忆文件仍然可读
- 避免了"数据囚禁"（Vendor Lock-in）

**对比 Claude Code / Codex：**

Claude Code 和 Codex 没有专门的记忆层，它们依赖：
- 工作区文件（代码、文档）
- 用户提供的上下文（Prompt）
- 临时的会话历史

这种方式的问题是：
- 没有结构化的知识积累
- 跨会话的记忆完全依赖用户手动管理
- 没有语义搜索能力

### 3.2 混合搜索的工程智慧

OpenClaw 采用 **向量搜索 + BM25 全文搜索** 的混合方案，这是经过深思熟虑的工程决策：

**向量搜索的优势：**
- 语义匹配："如何部署网关" ≈ "gateway setup guide"
- 容错性：拼写错误、同义词都能匹配
- 抽象能力：理解概念而非字面

**向量搜索的劣势：**
- 对精确ID、代码符号、错误信息弱
- 计算成本高（需要嵌入模型）
- 对短查询效果差

**BM25 全文搜索的优势：**
- 精确匹配：ID、代码符号、错误信息
- 速度快：基于倒排索引
- 可解释：匹配的关键词高亮

**BM25 的劣势：**
- 无法理解同义词
- 对语义相似但用词不同的情况无效

**OpenClaw 的融合策略：**

```
finalScore = vectorWeight * vectorScore + textWeight * textScore

默认：vectorWeight = 0.7, textWeight = 0.3
```

这表示 OpenClaw 更信任语义匹配（70%），但保留 30% 给关键词匹配来捕捉精确信息。

**实际场景示例：**

| 查询 | 向量搜索 | BM25 | 混合结果 |
|-----|---------|------|---------|
| "如何部署网关" | 匹配 "gateway setup guide" | 匹配包含"部署"的文档 | ✅ 最佳：语义+关键词都命中 |
| "error 0x80070005" | ❌ 弱 | ✅ 强 | ✅ BM25 拯救精确错误码 |
| "类似于 Kafka 的消息队列" | ✅ 强（匹配 "RabbitMQ"） | ❌ 弱（无 Kafka 关键词） | ✅ 向量理解同义概念 |

这种混合方法让 OpenClaw 在 **语义理解** 和 **精确检索** 之间取得了平衡，而大多数其他工具（Claude Code、Codex）根本没有这种能力。

### 3.3 自动 Memory Flush 的鲁棒性设计

OpenClaw 的 **预 Compaction Memory Flush** 是一个被低估但极其重要的设计：

**问题背景：**

LLM 会话有上下文长度限制（比如 128K、200K tokens）。当会话接近这个限制时，OpenClaw 必须 "compaction"（压缩）上下文——丢弃最早的消息以腾出空间。

**风险：**

如果 compaction 把重要信息丢弃了，而 Agent 没有提前把它保存到长期记忆，那么这些信息就永远丢失了。

**OpenClaw 的解决方案：**

```
触发条件：session token count > contextWindow - reserveTokensFloor - softThresholdTokens

          ↓

系统发送特殊提示（silent turn）：
"Session nearing compaction. Store durable memories now."

          ↓

Agent 决定：
- 如果有重要信息 → 写入 memory/YYYY-MM-DD.md
- 如果没有 → 回复 NO_REPLY（用户无感知）

          ↓

Compaction 安全执行，重要信息已持久化
```

**为什么这是鲁棒性设计：**

1. **主动性**：不是等到 compaction 后再抢救，而是提前预警
2. **Agent 自主性**：让 Agent 自己决定什么值得保存（比硬编码规则更灵活）
3. **透明性**：用户通常不会感知到这个机制（NO_REPLY），除非 Agent 决定写入
4. **安全性**：即使 Agent 不响应，系统也会继续 compaction（不会阻塞）

**对比其他工具：**

- **Claude Code**：用户需要手动运行 `/new` 来归档会话，没有自动 flush 机制
- **Codex**：没有会话管理，每次交互都是独立的

这个设计体现了 OpenClaw **对"记忆丢失"问题的深度思考**，而其他工具基本忽视了这个问题。

### 3.4 模块化与可扩展性的架构优势

OpenClaw 的记忆系统不是单体的，而是**模块化、可插拔的**：

**存储层可替换：**

```
默认：SQLite + 本地嵌入模型
   ↓
可选：QMD (高级混合搜索)
   ↓
可选：纯远程 (OpenAI/Gemini 嵌入 API)
```

**嵌入模型可配置：**

```
本地：node-llama-cpp (GGUF 模型，自动下载)
远程：OpenAI text-embedding-3-small
远程：Gemini embedding-001
远程：Voyage AI
自定义：OpenAI-compatible 端点
```

**搜索策略可调整：**

```json5
{
  query: {
    hybrid: {
      enabled: true,
      vectorWeight: 0.7,  // 可调整
      textWeight: 0.3,
      candidateMultiplier: 4
    }
  }
}
```

**为什么这很重要：**

1. **适应不同场景**：
   - 个人用户：本地模型，保护隐私
   - 团队：远程 API，快速部署
   - 企业：QMD 后端，高级搜索

2. **未来可扩展**：
   - 新的嵌入模型出现？添加 provider 即可
   - 新的搜索算法？替换 query engine 即可
   - 新的存储后端？实现 storage interface 即可

3. **避免 Vendor Lock-in**：
   - 核心数据是 Markdown 文件，随时可迁移
   - 不依赖特定云服务的 API

**对比其他工具：**

- **Claude Code**：封闭系统，无法替换记忆后端或嵌入模型
- **Codex**：更简单，没有专门的记忆系统

OpenClaw 的模块化设计体现了**工程上的成熟度和对未来的预留**。

---

## 四、详细对比表：OpenClaw vs 其他 Agent 的记忆系统

### 4.1 架构层对比

| 特性 | OpenClaw | Claude Code | Codex | Superpowers |
|-----|----------|-------------|-------|-------------|
| **记忆作为核心功能** | ✅ 是 | ⚠️ 次要 | ❌ 无 | ❌ 无 |
| **存储格式** | Markdown | Git + 代码 | 无 | 不涉及 |
| **索引系统** | SQLite + 可选 QMD | 无 | 无 | 无 |
| **嵌入模型选择** | 本地/远程 可选 | 固定 | 无 | 无 |
| **搜索算法** | 向量+BM25 混合 | 无 | 无 | 无 |
| **模块化程度** | 高（可替换后端） | 低（封闭） | 低 | 中（方法论） |

### 4.2 功能层对比

| 功能 | OpenClaw | Claude Code | Codex | Superpowers |
|-----|----------|-------------|-------|-------------|
| **语义搜索** | ✅ memory_search | ❌ 无 | ❌ 无 | ❌ 无 |
| **精确读取** | ✅ memory_get | ❌ 手动打开文件 | ❌ 无 | ❌ 无 |
| **自动预 compaction flush** | ✅ 自动触发 | ❌ 手动 /new | ❌ 无 | ❌ 无 |
| **会话日志索引** | ✅ 可选（实验性） | ❌ 仅归档 | ❌ 无 | ❌ 无 |
| **跨 Agent 记忆共享** | ✅ 通过文件系统 | ❌ 无 | ❌ 无 | ❌ 无 |
| **子 Agent 会话管理** | ✅ sessions_spawn | ⚠️ 有限 | ❌ 无 | ❌ 无 |

### 4.3 用户体验层对比

| 体验维度 | OpenClaw | Claude Code | Codex | Superpowers |
|---------|----------|-------------|-------|-------------|
| **配置复杂度** | 高（丰富选项） | 低（开箱即用） | 极低 | 中（需理解方法论） |
| **隐私控制** | ✅ 本地模型可选 | ⚠️ 依赖云服务 | ❌ 完全云端 | 不涉及 |
| **迁移难度** | 低（Markdown 通用） | 中（Git 历史） | 无 | 不涉及 |
| **学习曲线** | 陡峭 | 平缓 | 平坦 | 陡峭 |
| **适用场景** | 长期知识管理 | 日常编程辅助 | 快速代码生成 | 系统化开发流程 |

---

## 五、OpenClaw 记忆系统的核心优势总结

### 5.1 为什么 OpenClaw 的设计更先进？

**1. 记忆作为一等公民**

其他工具把记忆当作副产品，OpenClaw 把记忆当作核心功能。这体现在：
- 专门的 memory 配置文件和 CLI 命令
- 独立的索引和搜索系统
- 自动化的记忆生命周期管理

**2. 分层架构的鲁棒性**

```
真相层（Markdown）← 永远不丢失
    ↓
索引层（SQLite/QMD）← 可重建
    ↓
接口层（Tools）← 可替换
```

即使索引损坏，Markdown 文件依然存在；即使工具接口变化，文件格式通用。

**3. 主动防御而非被动补救**

预 compaction flush 机制是典型的"预防胜于治疗"设计：
- 不是等数据丢失后再抢救
- 而是在危险发生前主动保存
- 让 Agent 自主决定什么是重要的

**4. 模块化带来的选择权**

用户可以根据场景选择：
- 隐私优先 → 本地嵌入模型
- 性能优先 → 远程 API
- 搜索质量优先 → QMD 后端

这种"不替用户做决定"的设计理念体现了对多样性的尊重。

### 5.2 适用场景建议

| 场景 | 推荐工具 | 理由 |
|-----|---------|------|
| 长期知识管理、研究笔记 | **OpenClaw** | 语义搜索 + 持久化 + 隐私控制 |
| 日常编程辅助、快速原型 | Claude Code | 开箱即用，无需配置 |
| 简单代码生成、单次任务 | Codex | 极简，无负担 |
| 系统化团队开发流程 | Superpowers | 方法论框架，规范团队行为 |
| 跨会话的复杂项目追踪 | **OpenClaw** | 子 Agent + 记忆持久化 + 语义检索 |

---

## 六、附录：相关配置与命令速查

### OpenClaw 记忆相关 CLI

```bash
# 查看记忆系统状态
openclaw memory status
openclaw memory status --deep        # 深度检查（包括向量和嵌入）
openclaw memory status --deep --index # 如果索引 dirty 则重建

# 手动触发索引
openclaw memory index
openclaw memory index --verbose

# 搜索记忆
openclaw memory search "你的查询"

# 查看特定 Agent 的记忆状态
openclaw memory status --agent main
```

### 关键配置项（config.json5）

```json5
{
  agents: {
    defaults: {
      // 记忆搜索配置
      memorySearch: {
        enabled: true,
        provider: "openai",  // 或 "gemini", "local"
        model: "text-embedding-3-small",
        
        // 混合搜索权重
        query: {
          hybrid: {
            enabled: true,
            vectorWeight: 0.7,
            textWeight: 0.3
          }
        },
        
        // 本地模型配置（如果选择 local provider）
        local: {
          modelPath: "hf:ggml-org/embeddinggemma-300M-GGUF/embeddinggemma-300M-Q8_0.gguf"
        },
        
        // 远程 API 配置
        remote: {
          apiKey: "YOUR_API_KEY",
          batch: { enabled: true, concurrency: 2 }
        }
      },
      
      // Compaction 前的 memory flush 配置
      compaction: {
        reserveTokensFloor: 20000,
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 4000,
          systemPrompt: "Session nearing compaction. Store durable memories now.",
          prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."
        }
      }
    }
  }
}
```

---

> 🦐 **虾哥注**：本报告基于 OpenClaw v3.x 文档和源码分析。如需最新信息，请参考官方文档：https://docs.openclaw.ai

---

*分析完成时间：2026-02-08*  
*作者：虾哥 (Clawdbot)*  
*仓库：https://github.com/T0UGH/brother-xia-notes*
