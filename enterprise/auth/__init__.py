"""
插件式认证策略 — 接口定义
"""
from typing import Dict, Optional


class AuthProvider:
    """认证策略基类"""
    
    name = "base"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config or {}
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        """修改请求头以完成认证。返回修改后的 headers。"""
        raise NotImplementedError
    
    @classmethod
    def from_env(cls) -> "AuthProvider":
        """从环境变量创建认证实例"""
        import os
        return cls(os.environ)


def get_provider(name: str, config: Optional[Dict[str, str]] = None) -> AuthProvider:
    """根据名称获取认证策略实例"""
    from .none import NoAuthProvider
    from .basic import BasicAuthProvider
    from .bearer import BearerAuthProvider
    from .apikey import ApiKeyAuthProvider
    
    providers = {
        "none": NoAuthProvider,
        "basic": BasicAuthProvider,
        "bearer": BearerAuthProvider,
        "apikey": ApiKeyAuthProvider,
    }
    
    # rsa_two_step 仅在显式导入时可用（仅供学习参考）
    try:
        from .rsa_two_step import RsaTwoStepAuthProvider
        providers["rsa_two_step"] = RsaTwoStepAuthProvider
    except ImportError:
        pass
    
    cls = providers.get(name)
    if not cls:
        raise ValueError(f"Unknown auth provider: {name}, available: {list(providers.keys())}")
    return cls(config)
