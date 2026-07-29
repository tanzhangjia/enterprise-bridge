#!/usr/bin/env python3
"""
自定义适配器示例 — 连接一个假设的 HR API 系统

这个示例展示了：
1. 如何使用 HttpClient 连接真实 API
2. 如何使用 Bearer Token 认证
3. 如何处理不同的 API 格式

⚠️ 仅供学习参考

使用方式：
  export HR_API_BASE_URL=https://api.example.com
  export HR_API_KEY=your-token-here
  python3 -m enterprise hr user-list
  python3 -m enterprise hr user-get --user-id 123
"""

# 当适配器放在 enterprise/adapters/hr/ 下时，只需提供 register() 函数

from enterprise.models import SystemDef, ActionDef, ApiResult
from enterprise.registry import register_system
from enterprise.client import HttpClient


def handle_request(action: str, args: dict) -> ApiResult:
    """处理 HR 系统的所有操作"""
    import os
    
    base_url = os.environ.get("HR_API_BASE_URL")
    api_key = os.environ.get("HR_API_KEY")
    
    if not base_url:
        return ApiResult(success=False, error="请设置 HR_API_BASE_URL 环境变量")
    
    client = HttpClient(
        base_url=base_url,
        auth_type="bearer",
        auth_config={"token": api_key},
        max_retries=2,
    )
    
    if action == "user_list":
        response = client.get("/api/hr/users")
        return response
    
    if action == "user_get":
        uid = args.get("user_id")
        if not uid:
            return ApiResult(success=False, error="缺少 user_id 参数")
        response = client.get(f"/api/hr/users/{uid}")
        return response
    
    if action == "user_search":
        keyword = args.get("keyword", "")
        response = client.get("/api/hr/users/search", params={"q": keyword})
        return response
    
    return ApiResult(success=False, error=f"未知操作: {action}")


def register():
    """注册 HR 适配器"""
    register_system(SystemDef(
        name="hr",
        display_name="HR System",
        description="人力资源系统接口（示例适配器）",
        env_vars={
            "HR_API_BASE_URL": "API 地址（必填）",
            "HR_API_KEY": "Bearer Token（必填）",
        },
        actions=[
            ActionDef(name="user_list", help="列出所有员工"),
            ActionDef(name="user_get", help="查询员工信息", params=[
                {"name": "user_id", "type": "string", "required": True, "help": "员工 ID"},
            ]),
            ActionDef(name="user_search", help="搜索员工", params=[
                {"name": "keyword", "type": "string", "required": True, "help": "搜索关键词"},
            ]),
        ],
        handler=handle_request,
        auth_type="bearer",
    ))


if __name__ == "__main__":
    # 直接测试（需要设置环境变量）
    import sys
    register()
    from enterprise import cli
    cli.main()
