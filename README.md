# Enterprise Bridge

🔗 企业系统集成脚手架 — 一个通用的 REST API 集成框架，支持 CLI / MCP / OpenClaw Skill 三种使用方式。

## 特点

- **纯 Python 3，零外部依赖** — 标准库 + openssl（仅某些认证需要）
- **插件式认证** — 内置多种认证策略，可自定义
- **业务适配器** — 每个系统只需实现一个适配器注册函数
- **三种接口** — CLI + MCP Server + OpenClaw Skill
- **仅供学习** — 框架代码不包含任何企业系统的专有逻辑

## 快速开始

```bash
# 安装（无需安装，直接从目录运行）
cd enterprise-bridge

# 查看可用系统
python3 -m enterprise.cli --list-systems

# 操作演示系统
python3 -m enterprise.cli demo user-list
python3 -m enterprise.cli demo workflow-list --user-id "u001"

# 启动 MCP Server
python3 -m mcp.server demo

# MCP Server 交互
python3 -m mcp.server demo --interactive  # 或直接用 mcp-cli 客户端
```

## 架构

```
enterprise-bridge/
├── enterprise/
│   ├── __init__.py          # 核心库导出
│   ├── client.py            # 抽象 HTTP 客户端（重试、超时、日志）
│   ├── cli.py               # 统一 CLI 入口
│   ├── registry.py           # 适配器注册与发现
│   ├── auth/
│   │   ├── __init__.py       # 认证策略接口
│   │   ├── base.py           # 基类
│   │   ├── none.py           # 无认证
│   │   ├── basic.py          # HTTP Basic Auth
│   │   ├── bearer.py         # Bearer Token
│   │   ├── apikey.py         # API Key（Header/Query）
│   │   └── rsa_two_step.py   # 两步 RSA 认证模式（仅供学习参考）
│   ├── adapters/
│   │   ├── __init__.py       # 自动发现所有适配器
│   │   ├── demo/             # 演示系统（Mock）
│   │   │   ├── __init__.py   # register() 函数
│   │   │   └── api.py        # API 定义
│   │   └── (你的适配器)       # 按同样的结构添加
│   └── models.py             # 通用数据模型
├── mcp/
│   ├── __init__.py
│   ├── server.py             # MCP Server 实现
│   └── protocol.py           # MCP 协议工具
├── tests/
│   ├── test_client.py
│   ├── test_auth.py
│   └── test_registry.py
├── docs/
│   ├── guides/
│   │   └── add-adapter.md    # 添加适配器指南
│   └── architecture.md       # 架构文档
├── examples/
│   └── custom-adapter/       # 自定义适配器示例
├── SKILL.md                  # OpenClaw Skill 定义
└── README.md
```

## 使用方式

### 1. CLI 模式

```bash
# 格式：python3 -m enterprise.cli <system> <action> [参数]
python3 -m enterprise.cli demo user-list
python3 -m enterprise.cli demo workflow-list --user-id "u001"
python3 -m enterprise.cli demo user-get --user-id "u001"
```

### 2. MCP Server 模式

```bash
# 启动 MCP Server，暴露为 MCP 工具
python3 -m mcp.server demo

# MCP 客户端连接后可用工具：
# - demo_user_list
# - demo_workflow_list
# - demo_user_get
# - demo_workflow_approve
# - demo_api_call
```

### 3. OpenClaw Skill 模式

本 SKILL.md 文件即 OpenClaw Skill 定义，AI agent 加载后可自动识别：

```bash
# AI 可以通过 CLI 或 MCP 调用
python3 -m enterprise.cli <system> <action> [参数]
```

## 添加新系统适配器

创建一个新的适配器目录：

```
enterprise/adapters/my_system/
├── __init__.py   # register() 函数
└── api.py        # API 函数
```

`register()` 函数示例：

```python
def register(registry):
    registry.add_system(
        name="my_system",
        display_name="My System",
        description="Some enterprise system",
        env_vars={
            "MY_SYSTEM_BASE_URL": "Base URL",
            "MY_SYSTEM_API_KEY": "API Key",
        },
        actions=[
            {"name": "user-list", "help": "List users"},
            {"name": "workflow-list", "help": "List workflows"},
        ],
        handler=handle_request,
    )
```

详见 `docs/guides/add-adapter.md`。

## 认证策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `none` | 无需认证 | 内网、测试 |
| `basic` | HTTP Basic Auth | 老旧系统 |
| `bearer` | Bearer Token | OAuth2、JWT |
| `apikey` | API Key（Header/Query） | 大多数现代 API |
| `rsa_two_step` | 两步 RSA 注册认证 | 某些企业系统的认证模式（*仅供学习参考*） |

## 许可证

MIT
