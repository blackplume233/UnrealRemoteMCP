import asyncio
from pickle import FALSE, TRUE
import sys
import importlib
from typing import Optional
import uuid
from tools import tool_register
from tools.tool_register import register_all_tools
import unreal
import os


from foundation import log_handler
import warnings

try:
    from foundation.mcp_app import UnrealMCP
except Exception as e:
    import traceback

    unreal.log_error(f"Failed to import foundation.mcp_app: {str(e)}")
    unreal.log_error(traceback.format_exc())
    raise e

from foundation import global_context
import tools.common_tools as common_register
import tools.resource as resource_register
import tools.edit_tools as edit_register

# unreal.log("MCP Initialization Script Loaded")


global_context.reload_all_modules()

if global_context.get_counter() == 0:
    unreal.log("setup logging")
    log_handler.setup_logging()
    log_handler.setup_logging("uvicorn.error")

global_context.increment_counter()

# 忽略 Pydantic 的 'model_fields' 警告
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="Accessing the 'model_fields' attribute on the instance is deprecated",
)

# mcp SDK (stateless_http 模式) 每次请求创建的 sse_stream_reader 未被显式 aclose()，
# GC 回收时 anyio 会持续输出 ResourceWarning。属上游 bug，此处抑制。
warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r"Unclosed <MemoryObject",
)


def init_mcp() -> UnrealMCP:
    setting: unreal.MCPSetting = unreal.get_default_object(unreal.MCPSetting)
    unreal.log(f"init mcp")
    mcp = UnrealMCP("Remote Unreal MCP", host="127.0.0.1", port=setting.port,stateless_http=True)
    register_all_tools(mcp)
    mcp.init_unreal_mcp()

    global_context.set_mcp_instance(mcp)
    return mcp


def on_bridge(type: unreal.MCPBridgeFuncType, message: str):
    """C++ → Python bridge 入口。注意：只有 START 分支会阻塞（unreal_run 启动 async 事件循环）。"""
    # 统一声明一次，避免各分支重复类型标注导致 linter "declaration obscured" 警告
    instance: Optional[UnrealMCP] = None

    if type == unreal.MCPBridgeFuncType.START:
        instance = global_context.get_mcp_instance()
        if instance is not None:
            return False
        instance = init_mcp()
        instance.unreal_run()

    elif type == unreal.MCPBridgeFuncType.EXIT:
        # 只设标志位，由 async_run 循环检测后 await shutdown()；
        # 不直接调用 shutdown()——它是 async 函数，在 sync 上下文中调用会产生未 await 的协程
        instance = global_context.get_mcp_instance()
        if instance is not None:
            instance.should_exit = True
            global_context.set_mcp_instance(None)

    elif type == unreal.MCPBridgeFuncType.RELOAD:
        instance = global_context.get_mcp_instance()
        if instance is None:
            return True
        instance.clear_all()
        tool_register.reload_all_tools(instance)

    elif type == unreal.MCPBridgeFuncType.HEARTBEAT_PACKET:
        instance = global_context.get_mcp_instance()
        return instance is not None

    return True

def sync_tick() -> bool :
    instance: Optional[UnrealMCP] = global_context.get_mcp_instance()
    if instance is None:
        return False
    try:
        instance.sync_tick()
    except:
        unreal.log_error(f"tick with execption {e.args}")
    return True


def init_bridge():
    uuid_str: str = str(uuid.uuid4())
    context = unreal.MCPObject()
    context.bridge = unreal.MCPBridgeFuncDelegate()
    context.bridge.bind_callable(on_bridge)
    context.tick = unreal.MCPObjectEventFunction()
    context.tick.bind_callable(sync_tick)
    context.guid = uuid_str  # type: ignore
    # context.python_object_handle = unreal.create_python_object_handle(self)
    unreal.MCPSubsystem.get().setup_object(context)  # type: ignore


init_bridge()
