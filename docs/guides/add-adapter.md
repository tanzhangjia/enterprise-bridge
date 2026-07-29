# 添加新系统适配器

本指南说明如何为 Enterprise Bridge 添加一个新的企业系统适配器。

## 适配器结构

```
enterprise/adapters/your_system/
├── __init__.py   # register() 函数 + handler
└── (可选其他模块)
```

## 最小适配器

以下是一个完整的适配器示例：

```python
# enterprise/adapters/my_system/__init__.py
from enterprise.models import SystemDef, ActionDef, ApiResult
from enterprise.registry import register_system

def handle_request(action: str, args: dict) -> ApiResult:
    """处理所有操作请求。
    
    Args:
        action: snake_case 的操作名（CLI/MCP 会自动转换）
        args: snake_case 的参数名
    
    Returns:
        ApiResult(success=True, data={...}) 或 ApiResult(success=False, error="...")
    """
    
    if action == "user_list":
        # 调用你的 API
        # 可以使用 HttpClient 或直接 requests
        return ApiResult(success=True, data={"users": [...]})
    
    if action == "user_get":
        user_id = args.get("user_id")
        # ...
        return ApiResult(success=True, data={"id": user_id, "name": "..."})
    
    return ApiResult(success=False, error=f"未知操作: {action}")

def register():
    register_system(SystemDef(
        name="my_system",           # CLI 中使用的短名: python3 -m enterprise my_system user-list
        display_name="My System",   # 人类友好的显示名
        description="我的企业系统接口",
        env_vars={
            "MY_SYSTEM_BASE_URL": "系统地址（必填）",
            "MY_SYSTEM_API_KEY": "API 密钥",
        },
        actions=[
            ActionDef(name="user_list", help="列出所有用户"),
            ActionDef(name="user_get", help="查询用户信息", params=[
                {"name": "user_id", "type": "string", "required": True, "help": "用户 ID"},
            ]),
        ],
        handler=handle_request,
        auth_type="bearer",  # 可选：none / basic / bearer / apikey / rsa_two_step
    ))
```

## 使用 HttpClient

对于真实 HTTP API，可以使用内置的 HttpClient：

```python
from enterprise.client import HttpClient

def handle_request(action: str, args: dict) -> ApiResult:
    import os
    client = HttpClient(
        base_url=os.environ["MY_SYSTEM_BASE_URL"],
        auth_type="bearer",
        auth_config={"token": os.environ.get("MY_SYSTEM_API_KEY")},
    )
    
    if action == "user_list":
        return client.get("/api/users")
    
    if action == "user_get":
        return client.get(f"/api/users/{args['user_id']}")
```

## 命名约定

| 层 | 格式 | 示例 |
|---|---|---|
| ActionDef name | snake_case | `user_list` |
| Handler 参数 | snake_case | `user_id` |
| CLI action 输入 | 支持连字符 | `user-list` → 自动转 `user_list` |
| MCP tool name | snake_case | `demo_user_list` |
| MCP 参数 | snake_case 或连字符 | 都自动转下划线 |
| 环境变量 | UPPER_SNAKE_CASE | `MY_SYSTEM_BASE_URL` |
| 系统名 | snake_case | `my_system` |

## 认证策略配置

详见 `enterprise/auth/` 下的各策略实现。

| 策略 | 推荐变量（AUTH_*） | 兼容变量 |
|------|--------------------|----------|
| `none` | — | — |
| `basic` | `AUTH_USER` + `AUTH_PASS` | `BASIC_AUTH_USER` + `BASIC_AUTH_PASS` |
| `bearer` | `AUTH_TOKEN` | `BEARER_TOKEN` |
| `apikey` | `AUTH_KEY` + `AUTH_KEY_NAME` | `API_KEY` + `API_KEY_NAME` |
| `rsa_two_step` | `AUTH_BASE_URL` + `AUTH_APP_ID` | — （仅供学习参考） |

> 所有认证策略统一优先读取 `AUTH_*` 前缀的环境变量，兼容旧变量名。
> 通过 `auth_config` 字典传参的优先级高于环境变量。

## 打包

适配器不需要额外配置，只要放在 `enterprise/adapters/` 目录下即可被自动发现。

```bash
# 自动发现并注册
python3 -m enterprise --list-systems

# 使用
python3 -m enterprise my_system user-list

# 启动 MCP Server
python3 -m mcp.server my_system
```
