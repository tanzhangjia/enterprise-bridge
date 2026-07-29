"""
通用数据模型
"""
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ActionDef:
    """适配器中的一个操作定义"""
    name: str
    help: str
    params: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SystemDef:
    """系统适配器定义"""
    name: str
    display_name: str
    description: str
    env_vars: Dict[str, str]  # {变量名: 说明}
    actions: List[ActionDef]
    handler: Callable  # async def handler(action, args) -> dict
    auth_type: str = "none"
    default_env: Dict[str, str] = field(default_factory=dict)  # {变量名: 默认值}


@dataclass
class ApiResult:
    """统一的 API 返回"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {"success": self.success, "data": self.data, "error": self.error}
