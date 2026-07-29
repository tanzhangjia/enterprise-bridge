"""
无认证 — 直接发送请求
"""
from typing import Dict, Optional
from . import AuthProvider


class NoAuthProvider(AuthProvider):
    name = "none"
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        return headers
