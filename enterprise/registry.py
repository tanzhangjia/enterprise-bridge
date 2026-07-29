"""
适配器注册与发现 — 自动扫描、注册、按名称查找系统适配器
"""
import os, sys, importlib, inspect, pkgutil
from typing import Dict, Optional
from .models import SystemDef

_registry: Dict[str, SystemDef] = {}


def register_system(system: SystemDef):
    """注册一个系统适配器"""
    _registry[system.name] = system


def get_system(name: str) -> Optional[SystemDef]:
    """按名称查找系统适配器"""
    return _registry.get(name)


def list_systems() -> Dict[str, SystemDef]:
    """列出所有已注册的系统"""
    if not _registry:
        _discover_adapters()
    return dict(_registry)


def _discover_adapters():
    """自动发现 enterprise/adapters/ 下的所有适配器"""
    adapters_pkg_path = os.path.join(os.path.dirname(__file__), "adapters")
    if not os.path.isdir(adapters_pkg_path):
        return
    
    # 确保 adapters 包可导入
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    for importer, modname, ispkg in pkgutil.iter_modules([adapters_pkg_path]):
        if not ispkg:
            continue  # 只有包（目录）才被视为适配器
        try:
            # 确保路径正确
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            module = importlib.import_module(f"enterprise.adapters.{modname}")
            if hasattr(module, "register"):
                module.register()
                sys.stderr.write(f"[registry] ✓ 已加载适配器: {modname}\n")
        except Exception as e:
            sys.stderr.write(f"[registry] ✗ 加载适配器 {modname} 失败: {e}\n")


def init():
    """初始化注册中心"""
    _discover_adapters()
