"""
Demo 适配器 — 演示用 Mock 系统

这个适配器模拟了一个企业系统的常见接口（用户管理、流程审批等），
用于演示框架的使用方式和进行集成测试。

⚠️ 这只是一个演示示例，不连接任何真实系统。
"""
from enterprise.models import SystemDef, ActionDef, ApiResult
from enterprise.registry import register_system


# ── Mock 数据（仅供演示） ──

MOCK_USERS = {
    "u001": {"id": "u001", "name": "张三", "dept": "技术部", "role": "工程师"},
    "u002": {"id": "u002", "name": "李四", "dept": "市场部", "role": "经理"},
    "u003": {"id": "u003", "name": "王五", "dept": "财务部", "role": "主管"},
}

MOCK_WORKFLOWS = [
    {"id": "wf001", "name": "请假申请", "status": "审批中", "applicant": "张三", "created": "2026-07-29"},
    {"id": "wf002", "name": "费用报销", "status": "已通过", "applicant": "李四", "created": "2026-07-28"},
    {"id": "wf003", "name": "合同审批", "status": "待处理", "applicant": "王五", "created": "2026-07-27"},
]


def handle_request(action: str, args: dict) -> ApiResult:
    """处理 Demo 系统的所有操作。
    
    参数约定：action 和 args 的 key 均为 snake_case。
    CLI 和 MCP 入口会自动转换。
    """
    
    if action == "user_list":
        return ApiResult(success=True, data={"users": list(MOCK_USERS.values())})
    
    if action == "user_get":
        uid = args.get("user_id", "")
        user = MOCK_USERS.get(uid)
        if not user:
            return ApiResult(success=False, error=f"用户 {uid} 不存在")
        return ApiResult(success=True, data=user)
    
    if action == "workflow_list":
        return ApiResult(success=True, data={"workflows": MOCK_WORKFLOWS})
    
    if action == "workflow_get":
        wid = args.get("workflow_id", "")
        for w in MOCK_WORKFLOWS:
            if w["id"] == wid:
                return ApiResult(success=True, data=w)
        return ApiResult(success=False, error=f"流程 {wid} 不存在")
    
    if action == "workflow_approve":
        return ApiResult(success=True, data={
            "workflow_id": args.get("workflow_id"),
            "approved": args.get("approve", True),
            "opinion": args.get("opinion", ""),
            "message": "审批成功（演示）",
        })
    
    if action == "dept_list":
        return ApiResult(success=True, data={
            "departments": [
                {"id": "d001", "name": "技术部"},
                {"id": "d002", "name": "市场部"},
                {"id": "d003", "name": "财务部"},
            ]
        })
    
    if action == "api_call":
        return ApiResult(success=True, data={
            "echo_path": args.get("path"),
            "echo_method": args.get("method", "POST"),
            "echo_params": args.get("params"),
            "message": "通用接口调用（演示模式）",
        })
    
    return ApiResult(success=False, error=f"未知操作: {action}")


def register():
    """注册 Demo 适配器"""
    register_system(SystemDef(
        name="demo",
        display_name="Demo System",
        description="演示系统（Mock 数据，仅供学习参考）",
        env_vars={},
        actions=[
            ActionDef(name="user_list", help="列出所有用户"),
            ActionDef(name="user_get", help="查询用户信息", params=[
                {"name": "user_id", "type": "string", "required": True, "help": "用户 ID"},
            ]),
            ActionDef(name="workflow_list", help="列出流程", params=[
                {"name": "user_id", "type": "string", "required": False, "help": "按用户筛选"},
            ]),
            ActionDef(name="workflow_get", help="查询流程详情", params=[
                {"name": "workflow_id", "type": "string", "required": True, "help": "流程 ID"},
            ]),
            ActionDef(name="workflow_approve", help="审批流程", params=[
                {"name": "workflow_id", "type": "string", "required": True, "help": "流程 ID"},
                {"name": "approve", "type": "boolean", "required": False, "help": "是否通过"},
                {"name": "opinion", "type": "string", "required": False, "help": "审批意见"},
            ]),
            ActionDef(name="dept_list", help="列出所有部门"),
            ActionDef(name="api_call", help="通用接口调用", params=[
                {"name": "path", "type": "string", "required": True, "help": "API 路径"},
                {"name": "method", "type": "string", "required": False, "help": "HTTP 方法"},
                {"name": "params", "type": "string", "required": False, "help": "JSON 参数"},
            ]),
        ],
        handler=handle_request,
        auth_type="none",
    ))
