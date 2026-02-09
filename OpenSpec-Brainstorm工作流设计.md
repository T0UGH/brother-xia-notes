# OpenSpec + Brainstorm 融合设计

> 将 Superpower 的疯狂提问（Brainstorm）能力融入 OpenSpec，在正式写提案前充分挖掘需求。

---

## 核心思想

**传统流程的问题：**
```
用户: "我要做登录功能"
AI: 好的 → 直接写 proposal → 遗漏了很多细节
```

**Brainstorm-Driven 流程：**
```
用户: "我要做登录功能"
AI: 疯狂提问（Brainstorm）
  ├─ "支持手机号还是邮箱？"
  ├─ "需要 MFA 吗？"
  ├─ "密码复杂度要求？"
  ├─ "登录失败重试策略？"
  └─ "第三方登录（微信/Google）？"
→ 整理成需求澄清文档
→ 再写 proposal（基于充分理解）
```

---

## 工作流设计

### Schema 结构

```yaml
name: brainstorm-driven
version: 1
description: |
  Brainstorm-Driven Workflow:
  在写正式提案前，先通过疯狂提问充分挖掘需求

artifacts:
  # ========================================
  # Phase 1: Brainstorm（疯狂提问）
  # ========================================
  - id: brainstorm
    generates: brainstorm.md
    description: 需求探索与问题清单
    template: brainstorm.md
    
    instruction: |
      ## 角色定位
      你是一个需求挖掘专家。你的目标是在写正式提案前，
      通过疯狂提问来充分理解用户的真实需求。

      ## 任务
      针对用户的初始想法，从以下维度疯狂提问（至少 10 个问题）：

      ### 1. 功能范围
      - 核心功能是什么？
      - 明确不包含什么？
      - MVP 版本可以砍掉什么？

      ### 2. 用户视角
      - 目标用户是谁？
      - 他们的使用场景是什么？
      - 没有这个功能他们会怎么解决？

      ### 3. 技术约束
      - 需要集成现有系统吗？
      - 有性能要求吗（响应时间、并发）？
      - 技术栈有限制吗？

      ### 4. 安全与合规
      - 涉及敏感数据吗？
      - 需要审计日志吗？
      - 有合规要求吗（GDPR、等保）？

      ### 5. 维护与运营
      - 需要监控告警吗？
      - 有上线时间窗口要求吗？
      - 回滚策略是什么？

      ## 输出格式
      输出 brainstorm.md 包含：

      ```markdown
      # Brainstorm: [功能名称]

      ## 初始想法
      [用户最初的需求描述]

      ## 探索性问题

      ### 问题 1: [问题标题]
      - **问题**: [具体问题]
      - **为什么重要**: [为什么要问这个]
      - **可能的答案方向**: [A/B/C]

      ### 问题 2: ...

      ## 已澄清的需求
      [基于初步回答，已经明确的需求点]

      ## 待确认的问题
      [需要用户回答的关键问题]

      ## 下一步
      等待用户回答上述问题后，整理成正式 Proposal。
      ```

      ## 重要提醒
      - 不要假设，要提问
      - 多问 "如果...会怎样？"
      - 关注边界情况和异常流程
      - 把用户的 "我觉得" 变成 "具体是指...？"
    
    requires: []  # Brainstorm 是起点，无依赖

  # ========================================
  # Phase 2: Proposal（基于澄清的需求）
  # ========================================
  - id: proposal
    generates: proposal.md
    description: 正式提案
    template: proposal.md
    
    instruction: |
      ## 任务
      基于 Brainstorm 阶段的澄清，撰写正式的 Proposal。

      ## 关键原则
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
      - brainstorm  # Proposal 依赖于 Brainstorm 完成

  # ========================================
  # Phase 3+: 后续阶段（可选）
  # ========================================
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

## 交互流程示例

### 完整对话流程

```text
用户: 我要做一个用户登录功能

[执行 /opsx:new login-feature --schema brainstorm-driven]

AI: 好的，让我先深入了解一下这个需求。
    创建了 openspec/changes/login-feature/
    准备进入 Brainstorm 阶段...

AI: ## Brainstorm: 用户登录功能

    ### 初始想法
    做一个用户登录功能

    ### 探索性问题

    **问题 1: 登录方式**
    - 支持哪些登录方式？（手机号/邮箱/用户名/第三方）
    - 是否需要 MFA（短信/邮箱/Authenticator）？
    
    **问题 2: 密码策略**
    - 密码复杂度要求？（长度、特殊字符）
    - 密码加密方式？
    - 是否需要密码过期？
    
    **问题 3: 会话管理**
    - Token 类型？（JWT/Session）
    - 过期时间？
    - 是否支持多设备登录？
    
    **问题 4: 安全与风控**
    - 登录失败重试策略？（次数/锁定时间）
    - 是否需要验证码？（图形/滑块）
    - 异常登录检测？（异地/新设备）
    
    **问题 5: 用户体验**
    - 是否支持"记住我"？
    - 忘记密码流程？
    - 自动登录/静默刷新？

    ### 待确认的问题
    请回答以上问题，我将整理成正式的需求文档。

用户: 
- 登录方式：手机号 + 微信扫码
- 密码：至少8位，包含大小写
- Token：JWT，24小时过期
- 安全：连续5次失败锁定30分钟
- 其他：支持"记住我"7天

AI: 收到！基于你的回答，我整理了需求澄清文档。
    现在进入 Proposal 阶段...

    ## Proposal: 用户登录功能

    ### Why
    基于 Brainstorm 确认：用户需要安全、便捷的多方式登录...

    ### What
    1. 手机号 + 密码登录
    2. 微信扫码登录
    3. JWT 会话管理（24h）
    ...

    ### What Not
    - 不邮箱登录（本次）
    - 不 MFA 短信验证（后续迭代）
    ...

    ### Success Criteria
    - 登录成功率 > 95%
    - 平均登录时间 < 3秒
    - 安全审计无高危漏洞

    ### References
    - Brainstorm: [brainstorm.md](./brainstorm.md)

[后续可进入 Design → Tasks → Implement]
```

---

## 实施建议

### 1. 渐进式引入

不要一次性改变团队习惯，可以：
- 第 1 周：Brainstorm 阶段只问 3-5 个关键问题
- 第 2 周：增加到 8-10 个问题
- 第 3 周：引入完整的 Brainstorm 流程

### 2. 模板化常见问题

为常见功能类型创建 Brainstorm 模板：

```yaml
# openspec/schemas/brainstorm-driven/templates/brainstorm-login.md
# 登录功能的专门 Brainstorm 模板

## 登录功能检查清单

### 认证方式
- [ ] 手机号 + 验证码
- [ ] 邮箱 + 密码
- [ ] 第三方登录（微信/QQ/Google）
- [ ] SSO 企业登录

### 安全策略
- [ ] 密码复杂度要求
- [ ] 登录失败锁定策略
- [ ] 设备/IP 异常检测
- [ ] 敏感操作二次验证

### 用户体验
- [ ] 记住我（自动登录）
- [ ] 忘记密码流程
- [ ] 多端登录管理
- [ ] 无感知 Token 刷新
```

### 3. 与 AI 工具结合

可以把 Brainstorm 文档直接喂给 AI：

```markdown
基于以下 Brainstorm 文档，生成技术方案：

[粘贴 brainstorm.md 内容]

请生成：
1. 数据库 Schema
2. API 接口定义
3. 关键流程图
```

---

## 总结

通过将 **Brainstorm 阶段** 融入 OpenSpec，我们解决了传统流程的最大痛点：**在写提案前没有充分挖掘需求**。

**关键改进：**
- ✅ 从 "用户说啥我做啥" → "疯狂提问，挖掘真实需求"
- ✅ 从 "写代码时才发现问题" → "前期就把问题暴露出来"
- ✅ 从 "需求来回变更" → "早期就确认清楚"

**下一步行动：**
1. 在项目中创建 `brainstorm-driven` Schema
2. 选择一个即将开发的功能试用
3. 收集团队反馈，迭代优化

---

*有问题随时找我讨论！* 🚀
