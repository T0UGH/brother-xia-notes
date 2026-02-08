# OpenCode 项目深度分析

> 🚀 开源 AI 编程助手 —— Claude Code 的开源替代方案

---

## 一句话定位

**OpenCode 是一个 100% 开源的 AI 编程助手**，定位是开源版的 Claude Code，让开发者能在本地终端里用自然语言驱动代码编辑、重构、调试等开发工作。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **完全开源** | 代码、架构、协议全部公开，无黑盒 |
| **模型无关** | 支持 Claude、OpenAI、Google，甚至本地模型 |
| **终端优先** | 专注 TUI 界面，作者是 nvim 用户，追求极致终端体验 |
| **LSP 支持** | 开箱即用的语言服务器协议支持 |
| **C/S 架构** | 可在电脑上运行核心，手机远程控制前端 |

---

## 内置 Agents

OpenCode 内置两种 Agent 模式，可按 `Tab` 键切换：

| Agent | 模式 | 说明 |
|-------|------|------|
| **build** | 默认/全功能 | 能编辑文件、运行命令，执行实际开发任务 |
| **plan** | 只读/分析 | 用于代码探索和架构分析，编辑前会询问确认 |

此外还有个 **general** 子代理，用于复杂搜索和多步骤任务，可通过 `@general` 调用。

---

## 项目架构

```
opencode/
├── packages/          # Monorepo 包结构
│   ├── console/       # 终端 UI 应用
│   ├── web/           # Web 界面
│   └── ...
├── infra/             # 基础设施配置
├── github/            # GitHub Actions 和工作流
├── script/            # 开发脚本
├── specs/             # 功能规范和 RFC
├── themes/            # 主题文件
├── install            # 一键安装脚本
└── ...
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **运行时** | Bun (Node.js 替代) |
| **包管理** | Bun workspaces |
| **任务编排** | Turbo |
| **开发环境** | Nix |
| **部署** | SST (AWS) |
| **终端 UI** | Ink (React for Terminal) |

---

## 安装方式

```bash
# 一键安装
curl -fsSL https://opencode.ai/install | bash

# 包管理器
npm i -g opencode-ai@latest
brew install anomalyco/tap/opencode
scoop install opencode
```

---

## 与 Claude Code 的对比

| 维度 | OpenCode | Claude Code |
|------|----------|-------------|
| **开源** | ✅ 100% 开源 | ❌ 闭源 |
| **模型绑定** | 任意模型 | 仅 Anthropic |
| **终端体验** | 专注 TUI | TUI + GUI |
| **社区** | 开放共建 | Anthropic 主导 |
| **成本** | 可选本地模型 | API 计费 |

---

## 总结

OpenCode 的定位非常清晰：**做开源社区自己的 AI 编程助手**。

它的优势在于：
1. **无厂商锁定** —— 模型、部署、数据都自主可控
2. **社区驱动** —— 功能和方向由开发者需求决定
3. **终端原生** —— 为命令行重度用户优化

如果你正在用 Claude Code 但担心闭源风险，或者想用本地模型降低成本，OpenCode 是个值得关注的选择。

---

*分析完成于 2026-02-08 by 🦐 虾哥*
