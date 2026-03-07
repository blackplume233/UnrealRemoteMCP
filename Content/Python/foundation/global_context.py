
import asyncio
import importlib
import sys
from typing import Any, Optional
import unreal
import os

counter = 0# Static counter variable
loop = asyncio.SelectorEventLoop()
g_mcp_instance : Any = None

def get_counter() -> int:
    """Get the current value of the static counter."""
    global counter
    return counter

def increment_counter() -> int:
    """Increment the static counter by 1."""
    global counter
    counter += 1
    return counter

def rebuild_event_loop() -> None:
    """Rebuild the event loop."""
    global loop
    try:
        if loop is not None and loop.is_running():
            loop.run_forever()
            loop.stop()
            loop.close()
    except Exception as e:
        unreal.log(f"Error rebuilding event loop: {str(e)}")
    finally:
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)

def get_event_loop() -> asyncio.BaseEventLoop:
    """Get the current event loop name."""
    #asyncio.set_event_loop(loop)
    return loop

def reload_all_modules():
    """Reload all modules."""
    exclude_modules = ["foundation.global_context", "foundation.log_handler"]
    # 获取当前工作目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.path.abspath(os.path.join(current_dir, ".."))
    lib_dir = os.path.join(current_dir, "Lib")
    unreal.log(f"reload module from current_dir: {current_dir}")
    # 创建一个固定的模块列表
    modules_to_reload = list(sys.modules.items())
    for name, module in modules_to_reload:
        if name in exclude_modules:
            continue
        if hasattr(module, "__file__") and module.__file__ is not None:
            # 获取模块的绝对路径
            module_path = os.path.abspath(module.__file__)
            # 检查模块是否在当前目录或其子目录下
            if module_path.startswith(current_dir) and not module_path.startswith(lib_dir):
                try:
                    unreal.log(f"重新加载模块: {name} {module}")
                    importlib.reload(module)
                except Exception as e:
                    unreal.log(f"重新加载模块 {name} 失败: {str(e)}")

def reload_all_tool_modules():
    """Reload all modules."""
    exclude_modules = ["foundation.global_context", "foundation.log_handler"]
    # 获取当前工作目录
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.abspath(os.path.join(tools_dir, "..", "tools"))
    lib_dir = os.path.join(tools_dir, "Lib")
    unreal.log(f"reload module from current_dir: {tools_dir}\\tools")
    # 创建一个固定的模块列表
    modules_to_reload = list(sys.modules.items())
    for name, module in modules_to_reload:
        if name in exclude_modules:
            continue
        if hasattr(module, "__file__") and module.__file__ is not None:
            # 获取模块的绝对路径
            module_path = os.path.abspath(module.__file__)
            # 检查模块是否在当前目录或其子目录下
            if module_path.startswith(f'{tools_dir}') :
                try:
                    unreal.log(f"重新加载模块: {name} {module}")
                    importlib.reload(module)
                except Exception as e:
                    unreal.log(f"重新加载模块 {name} 失败: {str(e)}")



# 设置和获取 MCP 实例的全局变量与函数

def get_mcp_instance():
    global g_mcp_instance
    return g_mcp_instance

def set_mcp_instance(mcp_instance):
    global g_mcp_instance
    g_mcp_instance = mcp_instance
