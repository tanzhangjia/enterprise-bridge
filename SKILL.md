---
name: enterprise-bridge
description: Enterprise System Integration Scaffold — pluggable auth, API client, CLI, MCP Server & OpenClaw Skill
metadata:
  openclaw:
    emoji: 🔗
    requires:
      bins: [python3, openssl]
---

# 🔗 Enterprise Bridge — OpenClaw Skill

企业系统集成脚手架。适用于任何需要 REST API 接入的企业系统（OA、ERP、HR、财务等）。

**纯 Python 3，零外部依赖。** 提供 MCP Server 和 OpenClaw Skill 两种集成方式。

> ⚠️ 本仓库仅提供技术框架和示例代码，仅供学习参考。
> 对接真实系统时请遵守相关系统的使用协议和合规要求。

## 架构

```
┌─────────────────────────────────────────┐
│              MCP Server                  │  ← MCP 协议，给 AI 客户端用
│   (enterprise-bridge-mcp)               │
├─────────────────────────────────────────┤
│          OpenClaw Skill                  │  ← 本 SKILL.md
├─────────────────────────────────────────┤
│            CLI 入口                       │  ← 手动调试、脚本调用
│   (python3 -m enterprise.cli)            │
├─────────────────────────────────────────┤
│           核心库 enterprise               │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │ auth/     │  │ adapters/            │ │
│  │ 策略接口    │  │ 业务接口适配器         │ │
│  │ 实现插件化  │  │ 可替换/可扩展          │ │
│  └──────────┘  └──────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ client — HTTP 客户端                │ │
│  │ 连接池、重试、超时、日志              │ │
│  └────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│           第三方系统适配器                 │
│  📦 enterprise/adapters/                 │
│     ├── demo/        ← 演示用 Mock 系统   │
│     └── (你的适配器)                       │
└─────────────────────────────────────────┘
```

## 快速开始

```bash
# 查看演示（Mock 系统）
python3 -m enterprise.cli demo user-list
python3 -m enterprise.cli demo workflow-list

# 启动 MCP Server（用于 Claude Desktop / OpenClaw MCP 客户端）
python3 -m mcp.server demo

# 查看帮助
python3 -m enterprise.cli --help
```

## 添加新系统适配器

1. 在 `enterprise/auth/` 下实现认证策略（如有特殊认证）
2. 在 `enterprise/adapters/` 下创建适配器目录
3. 实现 `__init__.py` 中的 `register()` 函数
4. 系统自动发现并注册 CLI 命令和 MCP 工具

详见 `docs/guides/add-adapter.md`。
