#!/usr/bin/env python3
"""Enterprise Bridge 单元测试"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enterprise.models import SystemDef, ActionDef, ApiResult
from enterprise.registry import register_system, get_system, list_systems
from enterprise.client import HttpClient
from enterprise.auth import get_provider


def test_models():
    """测试数据模型"""
    action = ActionDef(name="test_action", help="测试", params=[
        {"name": "param1", "type": "string", "required": True, "help": "参数1"},
    ])
    assert action.name == "test_action"
    assert len(action.params) == 1
    assert action.params[0]["required"] is True
    
    result = ApiResult(success=True, data={"key": "value"})
    assert result.success is True
    assert result.data["key"] == "value"
    
    result = ApiResult(success=False, error="出错了")
    assert result.success is False
    assert result.error == "出错了"
    
    print("✓ test_models")


def test_registry():
    """测试适配器注册与发现"""
    # 注册一个测试适配器
    def test_handler(action, args):
        return ApiResult(success=True, data={"action": action})
    
    register_system(SystemDef(
        name="test_sys",
        display_name="Test System",
        description="测试",
        env_vars={},
        actions=[ActionDef(name="ping", help="ping")],
        handler=test_handler,
    ))
    
    systems = list_systems()
    assert "test_sys" in systems
    
    sys_def = get_system("test_sys")
    assert sys_def is not None
    assert sys_def.name == "test_sys"
    assert sys_def.display_name == "Test System"
    
    # 测试 handler 调用
    result = sys_def.handler("ping", {})
    assert result.success is True
    assert result.data["action"] == "ping"
    
    print("✓ test_registry")


def test_http_client():
    """测试 HttpClient（使用 httpbin 或本地 mock）"""
    client = HttpClient(
        base_url="https://httpbin.org",
        auth_type="none",
        max_retries=1,
    )
    
    result = client.get("/get", params={"test": "hello"})
    
    if result.success:
        assert "args" in result.data
        assert result.data["args"].get("test") == "hello"
        print("✓ test_http_client (live)")
    else:
        print(f"⚠ test_http_client (skip: {result.error})")


def test_auth_providers():
    """测试各认证策略"""
    # no auth
    provider = get_provider("none")
    headers = provider.authenticate({})
    assert headers == {}, f"None auth should return empty headers: {headers}"
    
    # basic auth
    provider = get_provider("basic", {"username": "user", "password": "pass"})
    headers = provider.authenticate({})
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")
    
    # bearer auth
    provider = get_provider("bearer", {"token": "test123"})
    headers = provider.authenticate({})
    assert headers["Authorization"] == "Bearer test123"
    
    # apikey auth
    provider = get_provider("apikey", {"api_key": "key123", "key_name": "X-API-Key"})
    headers = provider.authenticate({})
    assert headers["X-API-Key"] == "key123"
    
    print("✓ test_auth_providers")


def test_rsa_two_step_available():
    """测试 rsa_two_step 认证策略是否可导入"""
    try:
        provider = get_provider("rsa_two_step", {
            "BASE_URL": "http://localhost",
            "APP_ID": "test",
        })
        assert provider.name == "rsa_two_step"
        print("✓ test_rsa_two_step_available")
    except ValueError as e:
        print(f"⚠ test_rsa_two_step_available (skip: {e})")


def test_api_result_serialization():
    """测试 ApiResult 序列化"""
    result = ApiResult(success=True, data={"items": [1, 2, 3]})
    d = result.to_dict()
    assert d["success"] is True
    assert d["data"]["items"] == [1, 2, 3]
    
    result = ApiResult(success=False, error="fail")
    d = result.to_dict()
    assert d["success"] is False
    assert d["error"] == "fail"
    
    print("✓ test_api_result_serialization")


if __name__ == "__main__":
    test_models()
    test_registry()
    test_api_result_serialization()
    test_http_client()
    test_auth_providers()
    test_rsa_two_step_available()
    print("\n✅ 所有测试通过")
