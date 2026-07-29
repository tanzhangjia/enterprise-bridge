"""
API Key Authentication — Header 或 Query 参数方式
"""
from typing import Dict, Optional
from . import AuthProvider


class ApiKeyAuthProvider(AuthProvider):
    name = "apikey"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", self._auth_env("KEY", ""))
        self.key_name = self.config.get("key_name", self._auth_env("KEY_NAME", "X-API-Key"))
        self.in_header = self.config.get("in", "header")
    
    @staticmethod
    def _auth_env(key: str, default: str = "") -> str:
        import os
        return os.environ.get(f"AUTH_{key}", os.environ.get(f"API_{key}", default))
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        if self.in_header == "query":
            headers["__api_key_query__"] = f"{self.key_name}={self.api_key}"
        else:
            headers[self.key_name] = self.api_key
        return headers
