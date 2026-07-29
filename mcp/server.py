"""
MCP Server — 将企业系统适配器暴露为 MCP 工具

基于 MCP 协议（Model Context Protocol），
让 AI 客户端（Claude Desktop、OpenClaw MCP 等）能直接调用企业系统接口。

⚠️ 仅供学习参考

用法：
  python3 -m mcp.server <system>
  python3 -m mcp.server <system> --port 8000

环境变量：
  MCP_HOST=0.0.0.0
  MCP_PORT=8000
"""
import os, sys, json, logging

# 确保包可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enterprise.registry import list_systems, get_system, init
from enterprise.models import SystemDef, ActionDef

logger = logging.getLogger("mcp.server")


def build_mcp_json(system: SystemDef) -> dict:
    """
    构建 MCP Server 的 JSON 描述。
    遵循 MCP 协议格式，将适配器的每个操作暴露为一个 tool。
    """
    tools = []
    
    for action in system.actions:
        tool = {
            "name": f"{system.name}_{action.name}",
            "description": f"[{system.display_name}] {action.help}",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        }
        
        if action.params:
            required = []
            for p in action.params:
                pname = p.get("name", "")
                ptype = p.get("type", "string")
                prequired = p.get("required", False)
                phelp = p.get("help", "")
                
                # MCP 类型映射
                schema_type = {
                    "string": "string",
                    "integer": "integer",
                    "number": "number",
                    "boolean": "boolean",
                }.get(ptype, "string")
                
                tool["inputSchema"]["properties"][pname] = {
                    "type": schema_type,
                    "description": phelp,
                }
                
                if prequired:
                    required.append(pname)
            
            if required:
                tool["inputSchema"]["required"] = required
        
        tools.append(tool)
    
    server_info = {
        "name": f"enterprise-bridge-{system.name}",
        "version": "0.1.0",
        "description": f"Enterprise Bridge — {system.display_name} ({system.description})",
        "tools": tools,
    }
    
    return server_info


def handle_mcp_tool_call(system: SystemDef, tool_name: str, arguments: dict) -> dict:
    """
    处理 MCP 工具调用。
    将 MCP 的 tool_name 转换回适配器的 action + args。
    """
    prefix = f"{system.name}_"
    if not tool_name.startswith(prefix):
        return {"error": f"未知工具: {tool_name}"}
    
    action_name = tool_name[len(prefix):].replace("-", "_")
    
    # MCP 参数名转换：- 转 _（MCP 客户端可能用连字符参数名）
    cleaned_args = {}
    for k, v in arguments.items():
        cleaned_args[k.replace("-", "_")] = v
    
    # 执行适配器操作
    result = system.handler(action_name, cleaned_args)
    
    if not result.success:
        return {"error": result.error}
    
    return {"result": result.data}


def start_http_server(system: SystemDef, host: str = "0.0.0.0", port: int = 8000):
    """
    启动一个 HTTP 服务器，暴露 MCP 协议端点。
    使用标准库 http.server，零外部依赖。
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    server_info = build_mcp_json(system)
    
    class MCPHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            logger.info(f"{self.client_address[0]} - {format % args}")
        
        def _send_json(self, data: dict, status: int = 200):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        
        def do_GET(self):
            if self.path == "/" or self.path == "/server":
                # 获取 Server Info（含工具列表）
                self._send_json(server_info)
            elif self.path == "/health":
                self._send_json({"status": "ok", "system": system.name})
            else:
                self._send_json({"error": "Not found"}, 404)
        
        def do_POST(self):
            if self.path == "/call":
                # 调用工具
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    self._send_json({"error": "Invalid JSON"}, 400)
                    return
                
                tool_name = data.get("name", "")
                arguments = data.get("arguments", {})
                
                result = handle_mcp_tool_call(system, tool_name, arguments)
                self._send_json(result)
            else:
                self._send_json({"error": "Not found"}, 404)
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
    
    print(f"🔗 Enterprise Bridge MCP Server — {system.display_name}")
    print(f"   Server Info:  http://{host}:{port}/")
    print(f"   Health Check: http://{host}:{port}/health")
    print(f"   Call Tool:    POST http://{host}:{port}/call")
    print()
    print(f"   可用工具:")
    for tool in server_info["tools"]:
        print(f"     • {tool['name']}: {tool['description']}")
    print()
    print(f"⚠️  仅供学习参考")
    print()
    
    server = HTTPServer((host, port), MCPHandler)
    print(f"🚀 服务器已启动: http://{host}:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        server.server_close()


def start_stdio_server(system: SystemDef):
    """
    通过 STDIO 运行 MCP Server（适用于 Claude Desktop 等集成）。
    这是 MCP 协议的标准传输方式。
    """
    server_info = build_mcp_json(system)
    
    print(f"[enterprise-bridge] MCP STDIO Server — {system.display_name}", file=sys.stderr)
    print(f"[enterprise-bridge] 可用工具: {[t['name'] for t in server_info['tools']]}", file=sys.stderr)
    
    # 输出 Server Info（初始化时）
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "method": "server/info",
        "params": server_info,
    })
    print(init_msg, flush=True)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # MCP JSON-RPC 请求
        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})
        
        if method == "tools/list":
            # 返回工具列表
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": server_info["tools"]},
            }
            print(json.dumps(response), flush=True)
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = handle_mcp_tool_call(system, tool_name, arguments)
            
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            }
            print(json.dumps(response), flush=True)
        
        elif method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "serverInfo": {
                        "name": f"enterprise-bridge-{system.name}",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "tools": {},
                    },
                },
            }
            print(json.dumps(response), flush=True)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enterprise Bridge MCP Server")
    parser.add_argument("system", help="系统名称（如 demo）")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", "8000")))
    parser.add_argument("--host", default=os.environ.get("MCP_HOST", "0.0.0.0"))
    parser.add_argument("--stdio", action="store_true", help="使用 STDIO 模式（默认 HTTP）")
    parser.add_argument("--list-systems", action="store_true")
    
    args = parser.parse_args()
    
    # 初始化适配器
    init()
    
    if args.list_systems:
        print("可用系统:")
        for name in list_systems():
            print(f"  {name}")
        sys.exit(0)
    
    system = get_system(args.system)
    if not system:
        print(f"❌ 未知系统: {args.system}", file=sys.stderr)
        print("可用系统:", ", ".join(list_systems().keys()), file=sys.stderr)
        sys.exit(1)
    
    if args.stdio:
        start_stdio_server(system)
    else:
        start_http_server(system, args.host, args.port)


if __name__ == "__main__":
    main()
