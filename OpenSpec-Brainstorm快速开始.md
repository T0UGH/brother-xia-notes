# OpenSpec + Brainstorm 快速开始指南

> 5 分钟上手：在 OpenSpec 中融入疯狂提问能力

---

## 第一步：创建 Schema 目录

```bash
cd your-project
mkdir -p openspec/schemas/brainstorm-driven/templates
```

---

## 第二步：创建 schema.yaml

```yaml
# openspec/schemas/brainstorm-driven/schema.yaml
name: brainstorm-driven
version: 1
description: Brainstorm-Driven Workflow - 写提案前先疯狂提问

artifacts:
  # ========== Phase 1: Brainstorm ==========
  - id: brainstorm
    generates: brainstorm.md
    description: 需求探索与问题清单
    template: brainstorm.md
    
    instruction: |
      ## 任务：疯狂提问，挖掘真实需求
      
      针对用户的初始想法，从以下维度疯狂提问（至少 8-10 个）：
      
      ### 1. 功能范围
      - 核心功能是什么？明确不包含什么？
      - MVP 版本可以砍掉什么？
      
      ### 2. 用户视角
      - 目标用户是谁？使用场景是什么？
      - 没有这个他们会怎么解决？
      
      ### 3. 技术约束
      - 需要集成现有系统吗？
      - 有性能/安全/合规要求吗？
      
      ### 4. 维护与运营
      - 需要监控告警吗？
      - 回滚策略是什么？
      
      ## 输出格式
      创建 brainstorm.md 包含：
      1. 初始想法
      2. 探索性问题（至少 8 个，带可能答案方向）
      3. 待确认的问题清单
    
    requires: []

  # ========== Phase 2: Proposal ==========
  - id: proposal
    generates: proposal.md
    description: 基于澄清需求的正式提案
    template: proposal.md
    
    instruction: |
      ## 任务：基于 Brainstorm 撰写正式提案
      
      关键原则：
      - 引用 Brainstorm 中确认的需求点
      - 明确写出 "我们不做什么"（范围边界）
      - 包含可衡量的成功标准
      
      ## 输出结构
      1. Why - 为什么要做（引用 Brainstorm 的问题）
      2. What - 要做什么（基于澄清的需求）
      3. What Not - 明确不做
      4. Success Criteria - 如何衡量成功
      5. References - 链接到 Brainstorm 文档
    
    requires:
      - brainstorm

  # ========== Phase 3+: 后续（可选）==========
  - id: design
    generates: design.md
    description: 技术设计
    template: design.md
    requires:
      - proposal

  - id: tasks
    generates: tasks.md
    description: 实现任务
    template: tasks.md
    requires:
      - design

apply:
  requires: [tasks]
  tracks: tasks.md
```

---

## 第三步：创建 Templates

### brainstorm.md

```markdown
<!-- Brainstorm 模板 -->
# Brainstorm: [功能名称]

## 初始想法

[用户最初的需求描述]

---

## 探索性问题

### 问题 1: [问题类别]
- **问题**: [具体问题]
- **为什么重要**: [为什么要问这个]
- **可能的答案方向**:
  - A: [方向1]
  - B: [方向2]
  - C: [方向3]

### 问题 2: ...

[继续添加至少 8 个问题]

---

## 已澄清的需求

[基于初步回答，已经明确的需求点]

---

## 待确认的问题

[需要用户回答的关键问题，按优先级排序]

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 | [核心问题] | 决定架构方向 |
| P1 | [重要问题] | 影响实现复杂度 |

---

## 下一步

等待用户回答上述问题后，整理成正式 Proposal。
```

### proposal.md

```markdown
<!-- Proposal 模板 -->
# Proposal: [功能名称]

> 基于 Brainstorm: [brainstorm.md](./brainstorm.md)

---

## 1. Why - 为什么要做

### 问题背景
[引用 Brainstorm 中确认的核心问题]

### 不做会有什么影响
[引用 Brainstorm 中的影响分析]

---

## 2. What - 要做什么

### 功能范围

#### 包含（In Scope）
- [ ] [功能点1]
- [ ] [功能点2]

#### 不包含（Out of Scope）
- [ ] [明确不做的功能1] - 原因：[为什么不做]
- [ ] [明确不做的功能2] - 原因：[为什么不做]

### 用户故事

```gherkin
Given [前置条件]
When [用户行为]
Then [预期结果]
```

---

## 3. Success Criteria - 成功标准

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| [指标1] | [目标] | [如何测量] |
| [指标2] | [目标] | [如何测量] |

---

## 4. References

- Brainstorm: [brainstorm.md](./brainstorm.md)
- Related Specs: [链接到相关规格]

---

## Changelog

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| [日期] | v0.1 | 初始版本 | [作者] |
```

---

## 第四步：设置项目默认 Schema

```yaml
# openspec/config.yaml
schema: brainstorm-driven  # 使用新的 brainstorm 驱动工作流

context: |
  本项目的特点：
  - 追求需求理解透彻后再动手
  - 每个功能必须先经过 Brainstorm 阶段
  - 鼓励疯狂提问，不怕问题多

rules:
  brainstorm:
    - 至少提出 8 个探索性问题
    - 每个问题要有可能的答案方向
    - 明确标注待确认的问题优先级
  proposal:
    - 必须引用 brainstorm.md
    - 明确写出 In Scope 和 Out of Scope
    - 包含可衡量的成功标准
```

---

## 第五步：使用新的工作流

### 完整使用流程

```bash
# 1. 初始化项目（如果还没有）
openspec init

# 2. 开始一个新功能（会自动使用 brainstorm-driven）
openspec new change user-login

# 3. AI 会生成 brainstorm.md
#    - 疯狂提问（至少 8 个问题）
#    - 标注待确认的问题

# 4. 用户回答问题

# 5. 继续生成 proposal
/opsx:continue

# 6. 后续流程...（design → tasks → implement）
```

---

## 对话示例

### 完整的 AI 交互流程

```
用户: /opsx:new 用户登录功能

AI: 🧠 进入 Brainstorm 阶段...
    
    我创建了 openspec/changes/user-login/brainstorm.md
    
    针对"用户登录功能"，我有以下探索性问题：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 问题 1: 登录方式
   支持手机号、邮箱、用户名还是第三方（微信/Google）？
   
   可能方向：
   A) 仅手机号 + 验证码（最简单）
   B) 手机号/邮箱 + 密码 + 微信扫码
   C) 全支持（复杂度高）

📌 问题 2: 密码策略
   密码复杂度要求？是否需要历史密码检查？
   
   可能方向：
   A) 最少8位，包含大小写和数字
   B) 最少12位，必须包含特殊字符
   C) 使用 zxcvbn 强度检测

📌 问题 3: 多因素认证(MFA)
   是否需要短信/邮箱/Authenticator 二次验证？
   
   可能方向：
   A) 不需要（低风险场景）
   B) 管理员强制开启 MFA
   C) 用户可选开启

📌 问题 4: 会话管理
   Token 类型？过期时间？是否支持多设备？
   
   可能方向：
   A) JWT Access Token (2h) + Refresh Token (7d)
   B) Session + Cookie (24h)
   C) 短期 JWT (15min) + 自动刷新

📌 问题 5: 风控策略
   登录失败重试策略？异常登录检测？
   
   可能方向：
   A) 5次失败后锁定30分钟
   B) 渐进式延迟（1s → 2s → 4s...）
   C) 需要验证码 + 设备指纹分析

📌 问题 6: 用户体验
   "记住我"功能？自动登录？社交账号绑定？
   
   可能方向：
   A) 7天自动登录（设备级别）
   B) 每次都需要手动登录
   C) 智能判断（常用设备免登）

📌 问题 7: 国际化
   多语言支持？时区处理？合规要求？
   
   可能方向：
   A) 仅中文，国内部署
   B) 中英文，考虑 GDPR
   C) 多语言，全球合规

📌 问题 8: 监控与审计
   登录日志？异常告警？审计需求？
   
   可能方向：
   A) 基础日志（时间、IP、结果）
   B) 详细审计（设备信息、地理位置）
   C) 实时风控（异常检测、自动拦截）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 下一步：
   请回答以上问题（可以只选关键问题），
   我会整理成正式的需求文档。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[用户回答问题...]

AI: 感谢你的回答！基于澄清的需求，我现在创建正式 Proposal...
    
    生成了 openspec/changes/user-login/proposal.md
    
    包含：
    - Why：为什么要做这个功能（引用 Brainstorm 的问题）
    - What：明确的功能范围（基于你的选择）
    - What Not：明确不做（避免后期扯皮）
    - Success Criteria：可衡量的成功标准

[进入后续阶段：design → tasks → implement]
```

---

## 总结

通过将 **Brainstorm** 阶段融入 OpenSpec，我们实现了：

| 传统流程 | Brainstorm-Driven 流程 |
|----------|------------------------|
| 直接写 Proposal | 先疯狂提问，澄清需求 |
| 后期发现遗漏 | 早期暴露问题 |
| 需求来回变更 | 前期就确认清楚 |
| AI 被动接受 | AI 主动挖掘 |

**核心设计：**

```
brainstorm（疯狂提问）→ proposal（基于澄清的需求）→ design → tasks → implement
```

现在就可以开始试用！🚀
