#!/usr/bin/env python3
"""Enterprise Bridge 完整测试套件"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import patch, Mock, MagicMock
from urllib.error import HTTPError, URLError
from io import BytesIO

from enterprise.models import SystemDef, ActionDef, ApiResult
from enterprise.registry import register_system, get_system, list_systems
from enterprise.client import HttpClient
from enterprise.auth import get_provider, AuthProvider


class TestModels(unittest.TestCase):
    
    def test_action_def_basic(self):
        a = ActionDef(name="test", help="desc")
        self.assertEqual(a.name, "test")
        self.assertEqual(a.help, "desc")
        self.assertEqual(a.params, [])
    
    def test_action_def_with_params(self):
        a = ActionDef(name="test", help="desc", params=[
            {"name": "uid", "type": "string", "required": True},
            {"name": "opt", "type": "boolean", "required": False},
        ])
        self.assertEqual(len(a.params), 2)
        self.assertTrue(a.params[0]["required"])
        self.assertFalse(a.params[1]["required"])
    
    def test_api_result_success(self):
        r = ApiResult(success=True, data={"key": "val"})
        self.assertTrue(r.success)
        self.assertEqual(r.data["key"], "val")
        self.assertIsNone(r.error)
    
    def test_api_result_failure(self):
        r = ApiResult(success=False, error="kaboom")
        self.assertFalse(r.success)
        self.assertEqual(r.error, "kaboom")
        self.assertIsNone(r.data)
    
    def test_api_result_to_dict(self):
        r = ApiResult(success=True, data=[1, 2])
        d = r.to_dict()
        self.assertEqual(d["success"], True)
        self.assertEqual(d["data"], [1, 2])


class TestRegistry(unittest.TestCase):
    
    def setUp(self):
        import enterprise.registry as reg
        reg._registry.clear()
    
    def test_register_and_get(self):
        called = []
        def handler(action, args):
            called.append((action, args))
            return ApiResult(success=True, data={"echo": action})
        
        register_system(SystemDef(
            name="x", display_name="X", description="test", env_vars={},
            actions=[ActionDef(name="ping", help="ping")],
            handler=handler,
        ))
        
        sys_def = get_system("x")
        self.assertIsNotNone(sys_def)
        self.assertEqual(sys_def.name, "x")
        self.assertEqual(sys_def.display_name, "X")
        
        result = sys_def.handler("ping", {"a": 1})
        self.assertTrue(result.success)
        self.assertEqual(result.data["echo"], "ping")
        self.assertEqual(called, [("ping", {"a": 1})])
    
    def test_list_systems(self):
        register_system(SystemDef(
            name="a", display_name="A", description="", env_vars={},
            actions=[], handler=lambda a, kw: ApiResult(success=True, data={}),
        ))
        register_system(SystemDef(
            name="b", display_name="B", description="", env_vars={},
            actions=[], handler=lambda a, kw: ApiResult(success=True, data={}),
        ))
        systems = list_systems()
        self.assertIn("a", systems)
        self.assertIn("b", systems)
    
    def test_get_nonexistent(self):
        self.assertIsNone(get_system("nope"))


class TestHttpClient(unittest.TestCase):
    
    def _mock_resp(self, body: bytes):
        r = Mock()
        r.read = Mock(return_value=body)
        return r
    
    @patch("enterprise.client.urlopen")
    def test_get_success(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_resp(b'{"args":{"foo":"bar"}}')
        client = HttpClient("http://fake", auth_type="none", max_retries=1)
        result = client.get("/test", params={"foo": "bar"})
        self.assertTrue(result.success)
        self.assertEqual(result.data["args"]["foo"], "bar")
    
    @patch("enterprise.client.urlopen")
    def test_post(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_resp(b'{"form":{"x":"y"}}')
        client = HttpClient("http://fake", auth_type="none", max_retries=1)
        result = client.post("/test", params={"x": "y"})
        self.assertTrue(result.success)
        self.assertEqual(result.data["form"]["x"], "y")
    
    @patch("enterprise.client.urlopen")
    def test_404_returns_error(self, mock_urlopen):
        err = HTTPError("http://fake/404", 404, "Not Found", {}, BytesIO(b'{"error":"404"}'))
        mock_urlopen.side_effect = err
        client = HttpClient("http://fake", auth_type="none", max_retries=1)
        result = client.get("/test")
        self.assertFalse(result.success)
        self.assertIn("404", result.error)
    
    @patch("enterprise.client.urlopen")
    def test_retry_logic(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("timeout")
        client = HttpClient("http://fake", auth_type="none", max_retries=3, retry_delay=0.01)
        result = client.get("/test")
        self.assertFalse(result.success)
        self.assertEqual(mock_urlopen.call_count, 3)
    
    @patch("enterprise.client.urlopen")
    def test_4xx_no_retry(self, mock_urlopen):
        err = HTTPError("http://fake/403", 403, "Forbidden", {}, BytesIO(b'{"error":"no"}'))
        mock_urlopen.side_effect = err
        client = HttpClient("http://fake", auth_type="none", max_retries=3, retry_delay=0.01)
        result = client.get("/test")
        self.assertFalse(result.success)
        self.assertEqual(mock_urlopen.call_count, 1)
    
    @patch("enterprise.client.urlopen")
    def test_raw_response(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_resp(b'{"raw":"data"}')
        client = HttpClient("http://fake", auth_type="none", max_retries=1)
        result = client.get("/test", raw_response=True)
        self.assertTrue(result.success)
        self.assertIsInstance(result.data, str)
    
    @patch("enterprise.client.urlopen")
    def test_auth_integration(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_resp(
            b'{"headers":{"Authorization":"Bearer my-token"}}'
        )
        client = HttpClient("http://fake", auth_type="bearer",
                            auth_config={"token": "my-token"}, max_retries=1)
        result = client.get("/headers")
        self.assertTrue(result.success)
        self.assertIn("my-token", str(result.data))
    
    @patch("enterprise.client.urlopen")
    def test_retry_on_503(self, mock_urlopen):
        err = HTTPError("http://fake/503", 503, "Service Unavailable", {}, BytesIO(b''))
        mock_urlopen.side_effect = err
        client = HttpClient("http://fake", auth_type="none", max_retries=2, retry_delay=0.01)
        result = client.get("/status/503")
        self.assertFalse(result.success)


class TestAuthProviders(unittest.TestCase):
    
    def test_none(self):
        p = get_provider("none")
        h = p.authenticate({"X": "1"})
        self.assertEqual(h, {"X": "1"})
    
    def test_basic(self):
        p = get_provider("basic", {"username": "alice", "password": "secret"})
        h = p.authenticate({})
        self.assertIn("Authorization", h)
        self.assertTrue(h["Authorization"].startswith("Basic "))
    
    def test_bearer(self):
        p = get_provider("bearer", {"token": "mytoken"})
        h = p.authenticate({})
        self.assertEqual(h["Authorization"], "Bearer mytoken")
    
    def test_apikey_header(self):
        p = get_provider("apikey", {"api_key": "k123", "key_name": "X-Key"})
        h = p.authenticate({})
        self.assertEqual(h["X-Key"], "k123")
    
    def test_apikey_query(self):
        p = get_provider("apikey", {"api_key": "k123", "key_name": "key", "in": "query"})
        h = p.authenticate({})
        self.assertNotIn("key", h)
        self.assertIn("__api_key_query__", h)
        self.assertEqual(h["__api_key_query__"], "key=k123")
    
    def test_rsa_two_step_available(self):
        try:
            p = get_provider("rsa_two_step", {"BASE_URL": "http://x", "APP_ID": "test"})
            self.assertEqual(p.name, "rsa_two_step")
        except ValueError:
            self.fail("rsa_two_step should be importable")
    
    def test_unknown_provider(self):
        with self.assertRaises(ValueError):
            get_provider("nope")


class TestApiResultSerialization(unittest.TestCase):
    
    def test_success_to_dict(self):
        r = ApiResult(success=True, data={"items": [1, 2, 3]})
        d = r.to_dict()
        self.assertEqual(d["success"], True)
        self.assertEqual(d["data"]["items"], [1, 2, 3])
        self.assertIsNone(d.get("error"))
    
    def test_error_to_dict(self):
        r = ApiResult(success=False, error="fail")
        d = r.to_dict()
        self.assertEqual(d["success"], False)
        self.assertEqual(d["error"], "fail")


class TestSystemDef(unittest.TestCase):
    
    def test_system_def_defaults(self):
        def h(a, kw): return ApiResult(success=True, data={})
        s = SystemDef(
            name="test", display_name="Test", description="x",
            env_vars={"K": "desc"}, actions=[], handler=h,
        )
        self.assertEqual(s.auth_type, "none")
        self.assertEqual(s.default_env, {})
    
    def test_system_def_custom(self):
        def h(a, kw): return ApiResult(success=True, data={})
        s = SystemDef(
            name="t2", display_name="T2", description="x",
            env_vars={}, actions=[], handler=h,
            auth_type="bearer",
            default_env={"URL": "http://default"},
        )
        self.assertEqual(s.auth_type, "bearer")
        self.assertEqual(s.default_env["URL"], "http://default")


class TestMCP(unittest.TestCase):
    """MCP Server 关键函数的测试"""
    
    def setUp(self):
        import enterprise.registry as reg
        reg._registry.clear()
        
        def handler(action, args):
            if action == "echo":
                return ApiResult(success=True, data=args)
            if action == "fail":
                return ApiResult(success=False, error="boom")
            return ApiResult(success=False, error=f"unknown: {action}")
        
        register_system(SystemDef(
            name="test_sys", display_name="Test", description="x",
            env_vars={},
            actions=[
                ActionDef(name="echo", help="echo", params=[
                    {"name": "msg", "type": "string", "required": True},
                ]),
                ActionDef(name="fail", help="fail"),
            ],
            handler=handler,
        ))
        
        from mcp.server import build_mcp_json, handle_mcp_tool_call
        self.system = get_system("test_sys")
        self.build = build_mcp_json
        self.handle = handle_mcp_tool_call
    
    def test_build_mcp_json_has_tools(self):
        info = self.build(self.system)
        self.assertEqual(info["name"], "enterprise-bridge-test_sys")
        tool_names = [t["name"] for t in info["tools"]]
        self.assertIn("test_sys_echo", tool_names)
        self.assertIn("test_sys_fail", tool_names)
    
    def test_build_mcp_json_params(self):
        info = self.build(self.system)
        echo_tool = [t for t in info["tools"] if t["name"] == "test_sys_echo"][0]
        self.assertIn("msg", echo_tool["inputSchema"]["required"])
        self.assertEqual(
            echo_tool["inputSchema"]["properties"]["msg"]["type"], "string",
        )
    
    def test_handle_tool_call_echo(self):
        result = self.handle(self.system, "test_sys_echo", {"msg": "hello"})
        self.assertEqual(result["result"]["msg"], "hello")
    
    def test_handle_tool_call_fail(self):
        result = self.handle(self.system, "test_sys_fail", {})
        self.assertIn("error", result)
    
    def test_handle_tool_call_unknown(self):
        result = self.handle(self.system, "test_sys_nope", {})
        self.assertIn("error", result)
    
    def test_handle_tool_call_wrong_prefix(self):
        result = self.handle(self.system, "other_ping", {})
        self.assertIn("error", result)


class TestCLI(unittest.TestCase):
    """CLI 参数解析测试"""
    
    def test_parse_extra_args_simple(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args(["--user-id", "u001"])
        self.assertEqual(r, {"user_id": "u001"})
    
    def test_parse_extra_args_bool(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args(["--approve", "true", "--dry-run"])
        self.assertEqual(r, {"approve": True, "dry_run": True})
    
    def test_parse_extra_args_int(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args(["--limit", "100"])
        self.assertEqual(r, {"limit": 100})
    
    def test_parse_extra_args_json(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args(["--config", '{"key":"val"}'])
        self.assertEqual(r["config"], {"key": "val"})
    
    def test_parse_extra_args_mixed(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args([
            "--user-id", "u001",
            "--approve",
            "--opinion", "同意",
        ])
        self.assertEqual(r["user_id"], "u001")
        self.assertEqual(r["approve"], True)
        self.assertEqual(r["opinion"], "同意")
    
    def test_parse_extra_args_empty(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args([])
        self.assertEqual(r, {})
    
    def test_parse_extra_args_equals(self):
        from enterprise.cli import _parse_extra_args
        r = _parse_extra_args(["--user-id=u001", "--opinion=同意", "--count=3"])
        self.assertEqual(r, {"user_id": "u001", "opinion": "同意", "count": 3})


if __name__ == "__main__":
    unittest.main(verbosity=2)
