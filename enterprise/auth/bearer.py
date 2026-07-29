"""
Bearer Token Authentication
"""
from typing import Dict, Optional
from . import AuthProvider


class BearerAuthProvider(AuthProvider):
    name = "bearer"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.token = self.config.get("token", self._env("BEARER_TOKEN", ""))
    
    def _env(self, key: str, default: str = "") -> str:
        import os
        return os.environ.get(key, default)
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers["Authorization"] = f"Bearer {self.token}"
        return headers
