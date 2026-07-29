"""
抽象 HTTP 客户端 — 通用、可重试、可配置

设计目标：
- 零外部依赖（只用标准库 urllib）
- 自动重试（可配置重试次数和策略）
- 插件式认证
- 统一的请求/响应处理
- 日志输出
"""
import os, sys, json, time, logging
from typing import Dict, Any, Optional, Callable
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

from .auth import get_provider, AuthProvider
from .models import ApiResult

logger = logging.getLogger("enterprise.client")


class HttpClient:
    """通用的企业系统 HTTP 客户端"""
    
    def __init__(
        self,
        base_url: str,
        auth_type: str = "none",
        auth_config: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        user_agent: str = "EnterpriseBridge/0.1",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        
        self.auth: AuthProvider = get_provider(auth_type, auth_config)
        
        logger.debug(f"HttpClient initialized: base_url={base_url}, auth={auth_type}")
    
    def _build_url(self, path: str, query_params: Optional[Dict[str, str]] = None) -> str:
        url = f"{self.base_url}{path}"
        if query_params:
            url += "?" + urlencode(query_params)
        return url
    
    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        if extra_headers:
            headers.update(extra_headers)
        
        # 通过认证策略注入认证头
        headers = self.auth.authenticate(headers)
        
        # 处理 API Key 查询参数标记
        query_extra = None
        qk = headers.pop("__api_key_query__", None)
        if qk:
            query_extra = qk
        
        return headers, query_extra
    
    def request(
        self,
        path: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raw_response: bool = False,
    ) -> ApiResult:
        """执行 HTTP 请求，带重试逻辑"""
        headers, query_extra = self._build_headers(headers)
        
        # 构建 URL，含查询参数
        query_params = {}
        if method == "GET" and params:
            query_params.update(params)
        if query_extra:
            k, v = query_extra.split("=", 1)
            query_params[k] = v
        
        url = self._build_url(path, query_params if query_params else None)
        
        # 构建请求体
        data = None
        if method != "GET" and params:
            data = urlencode(params).encode()
        
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                req = Request(url, method=method, data=data)
                for k, v in headers.items():
                    req.add_header(k, v)
                
                logger.debug(f"[{attempt}/{self.max_retries}] {method} {url}")
                resp = urlopen(req, timeout=self.timeout)
                body = resp.read().decode("utf-8")
                
                if raw_response:
                    return ApiResult(success=True, data=body)
                
                try:
                    result = json.loads(body)
                except json.JSONDecodeError:
                    return ApiResult(success=True, data=body)
                
                return ApiResult(success=True, data=result)
            
            except HTTPError as e:
                last_error = e
                error_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
                logger.warning(f"[{attempt}/{self.max_retries}] HTTP {e.code}: {e.reason} — {error_body[:200]}")
                
                # 不重试 4xx（除非 429）
                if 400 <= e.code < 500 and e.code != 429:
                    return ApiResult(success=False, error=f"HTTP {e.code}: {error_body[:500]}")
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # 指数退避
            
            except URLError as e:
                last_error = e
                logger.warning(f"[{attempt}/{self.max_retries}] URLError: {e.reason}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))
            
            except Exception as e:
                last_error = e
                logger.error(f"[{attempt}/{self.max_retries}] Unexpected error: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))
        
        return ApiResult(success=False, error=f"请求失败（{self.max_retries} 次重试后）: {last_error}")
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kw) -> ApiResult:
        return self.request(path, method="GET", params=params, **kw)
    
    def post(self, path: str, params: Optional[Dict[str, Any]] = None, **kw) -> ApiResult:
        return self.request(path, method="POST", params=params, **kw)
    
    def put(self, path: str, params: Optional[Dict[str, Any]] = None, **kw) -> ApiResult:
        return self.request(path, method="PUT", params=params, **kw)
    
    def delete(self, path: str, params: Optional[Dict[str, Any]] = None, **kw) -> ApiResult:
        return self.request(path, method="DELETE", params=params, **kw)
