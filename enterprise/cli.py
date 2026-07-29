#!/usr/bin/env python3
"""
Enterprise Bridge CLI — 统一命令行入口

用法：
  python3 -m enterprise.cli <system> <action> [参数]
  python3 -m enterprise.cli --list-systems

示例：
  python3 -m enterprise.cli demo user-list
  python3 -m enterprise.cli demo user-get --user-id u001
  python3 -m enterprise.cli demo workflow-list
"""
import os, sys, json, argparse

# 确保包可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enterprise.registry import list_systems, get_system, init
from enterprise.models import SystemDef


def main():
    parser = argparse.ArgumentParser(
        description="🔗 Enterprise Bridge — 企业系统集成脚手架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list-systems", action="store_true",
        help="列出所有已注册的系统适配器"
    )
    parser.add_argument(
        "system", nargs="?",
        help="系统名称（如 demo）"
    )
    parser.add_argument(
        "action", nargs="?",
        help="操作名称（如 user-list）"
    )
    parser.add_argument(
        "extra", nargs=argparse.REMAINDER,
        help="操作参数（--key value 格式）"
    )
    
    args = parser.parse_args()
    
    # 初始化适配器注册中心
    init()
    
    if args.list_systems:
        systems = list_systems()
        if not systems:
            print("❌ 没有已注册的系统适配器")
            sys.exit(1)
        print("📋 已注册的系统适配器:\n")
        for name, sys_def in systems.items():
            print(f"  {name:<12} — {sys_def.display_name}")
            print(f"  {'':12} {sys_def.description}")
            print(f"  {'':12} 认证方式: {sys_def.auth_type}")
            print(f"  {'':12} 操作:")
            for act in sys_def.actions:
                print(f"  {'':12}   • {act.name:<18} {act.help}")
            print()
        sys.exit(0)
    
    if not args.system:
        parser.print_help()
        print("\n可用系统（--list-systems 查看详情）:")
        for name in list_systems():
            print(f"  {name}")
        sys.exit(1)
    
    system = get_system(args.system)
    if not system:
        print(f"❌ 未知系统: {args.system}")
        print("可用系统:", ", ".join(list_systems().keys()))
        sys.exit(1)
    
    if not args.action:
        print(f"系统: {system.display_name} ({system.name})")
        print(f"描述: {system.description}")
        print(f"可用操作:")
        for act in system.actions:
            print(f"  {act.name:<18} {act.help}")
        sys.exit(0)
    
    # 解析额外参数
    action_args = _parse_extra_args(args.extra)
    
    # 转换 action 名：CLI 中 action 接受连字符，自动转下划线
    action_name = args.action.replace("-", "_")
    
    # 执行操作
    result = system.handler(action_name, action_args)
    
    if not result.success:
        print(f"❌ {result.error}", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果
    print(json.dumps(result.data, indent=2, ensure_ascii=False))


def _parse_extra_args(extra: list) -> dict:
    """解析 --key value 格式的剩余参数"""
    params = {}
    i = 0
    while i < len(extra):
        arg = extra[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")  # CLI 风格转 snake_case
            if i + 1 < len(extra) and not extra[i+1].startswith("--"):
                val = extra[i+1]
                # 尝试解析为 JSON
                if val.lower() in ("true", "yes", "1"):
                    val = True
                elif val.lower() in ("false", "no", "0"):
                    val = False
                elif val.isdigit():
                    val = int(val)
                else:
                    try:
                        val = json.loads(val)
                    except (json.JSONDecodeError, ValueError):
                        pass
                params[key] = val
                i += 2
            else:
                params[key] = True
                i += 1
        else:
            i += 1
    return params


if __name__ == "__main__":
    main()
