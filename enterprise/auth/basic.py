"""
HTTP Basic Authentication
"""
import base64
from typing import Dict, Optional
from . import AuthProvider


class BasicAuthProvider(AuthProvider):
    name = "basic"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.username = self.config.get("username", self._auth_env("USER", ""))
        self.password = self.config.get("password", self._auth_env("PASS", ""))
    
    @staticmethod
    def _auth_env(key: str, default: str = "") -> str:
        import os
        return os.environ.get(f"AUTH_{key}", os.environ.get(f"BASIC_AUTH_{key}", default))
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        raw = f"{self.username}:{self.password}"
        encoded = base64.b64encode(raw.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"
        return headers
