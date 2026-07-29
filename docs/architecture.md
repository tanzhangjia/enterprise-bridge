# 架构文档

## 整体架构

```
用户层
├── 命令行 (CLI)           python3 -m enterprise.cli
├── MCP Server (HTTP)      python3 -m mcp.server
├── MCP Server (STDIO)     python3 -m mcp.server --stdio
└── OpenClaw Skill         SKILL.md

核心层 (enterprise/)
├── registry.py            适配器注册与自动发现
├── client.py              抽象 HTTP 客户端
├── models.py              通用数据模型
├── auth/                  插件式认证策略
│   ├── base.py            认证基类
│   ├── none.py            无认证
│   ├── basic.py           HTTP Basic Auth
│   ├── bearer.py          Bearer Token
│   ├── apikey.py          API Key
│   └── rsa_two_step.py    两步 RSA 认证模式（仅供学习参考）
└── adapters/              业务适配器
    ├── demo/              演示适配器
    └── (你的适配器)

协议层 (mcp/)
├── server.py              MCP Server 实现
└── protocol.py            MCP 协议工具
```

## 数据流

### CLI 调用

```
用户输入 → cli.py (参数解析) → adapter.handle(action, args) → ApiResult → JSON输出
```

### MCP 调用

```
外部 MCP 客户端 → HTTP POST /call → server.py (协议解析) → adapter.handle() → JSON Response
```

### 认证流程

```
使用者配置环境变量
    ↓
HttpClient 初始化 → 选择 AuthProvider
    ↓
每次请求 → auth.authenticate(headers) → 注入认证头
    ↓
发送 HTTP 请求
```

## 适配器生命周期

1. **自动发现**：`enterprise/adapters/` 下的包会被 `registry._discover_adapters()` 自动扫描
2. **注册**：每个适配器的 `register()` 函数被调用，将 `SystemDef` 注册到全局 registry
3. **使用**：CLI/MCP 通过 `registry.get_system(name)` 获取适配器定义并调用 handler

## 命名约定

| 组件 | 格式 | 示例 |
|------|------|------|
| 系统名 (name) | snake_case | `my_system` |
| 操作名 (action) | snake_case | `user_list` |
| 参数名 | snake_case | `user_id` |
| CLI action | 连字符友好 | `user-list` (自动转) |
| MCP tool | snake_case | `my_system_user_list` |
| 环境变量 | UPPER_SNAKE_CASE | `MY_API_KEY` |

## 设计原则

1. **零外部依赖** — 只用 Python 3 标准库（认证需要 openssl CLI 的除外）
2. **插件化** — 每个系统一个适配器，互不干扰
3. **松耦合** — 适配器不知道 CLI/MCP 的存在，只实现 handler
4. **安全** — 证书等敏感信息通过环境变量传入，不进代码
