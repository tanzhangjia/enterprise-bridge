"""
Bearer Token Authentication
"""
from typing import Dict, Optional
from . import AuthProvider


class BearerAuthProvider(AuthProvider):
    name = "bearer"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.token = self.config.get("token", self._auth_env("TOKEN", ""))
    
    @staticmethod
    def _auth_env(key: str, default: str = "") -> str:
        import os
        return os.environ.get(f"AUTH_{key}", os.environ.get(f"BEARER_{key}", default))
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers["Authorization"] = f"Bearer {self.token}"
        return headers
