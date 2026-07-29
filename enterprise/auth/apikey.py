"""
API Key Authentication — Header 或 Query 参数方式
"""
from typing import Dict, Optional
from . import AuthProvider


class ApiKeyAuthProvider(AuthProvider):
    name = "apikey"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", self._env("API_KEY", ""))
        self.key_name = self.config.get("key_name", self._env("API_KEY_NAME", "X-API-Key"))
        self.in_header = self.config.get("in", "header")  # "header" or "query"
    
    def _env(self, key: str, default: str = "") -> str:
        import os
        return os.environ.get(key, default)
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        if self.in_header == "query":
            # 标记为查询参数，调用方负责处理
            headers["__api_key_query__"] = f"{self.key_name}={self.api_key}"
        else:
            headers[self.key_name] = self.api_key
        return headers
