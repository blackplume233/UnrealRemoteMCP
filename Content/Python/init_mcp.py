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


def init_mcp() -> UnrealMCP:
    setting: unreal.MCPSetting = unreal.get_default_object(unreal.MCPSetting)
    # global_context.rebuild_event_loop()
    unreal.log(f"init mcp")
    mcp = UnrealMCP("Remote Unreal MCP", host="127.0.0.1", port=setting.port,stateless_http=True)
    register_all_tools(mcp)
    mcp.init_unreal_mcp()

    global_context.set_mcp_instance(mcp)
    return mcp


def on_bridge(type: unreal.MCPBridgeFuncType, message: str):

    # unreal.log("Bridge Message: " + message)
    # 特别注意，只有Start是在异步线程中执行的，该函数永远不会退出
    if type == unreal.MCPBridgeFuncType.START:
        instance: Optional[UnrealMCP] = global_context.get_mcp_instance()
        if not instance is None:
            return False
        instance = init_mcp()
        instance.unreal_run()
        pass

    if type == unreal.MCPBridgeFuncType.EXIT:
        instance: Optional[UnrealMCP] = global_context.get_mcp_instance()
        if not instance is None:
            instance.should_exit = True
            asyncio.wait_for(instance.shutdown(),100)
            global_context.set_mcp_instance(None)
        pass

    if type == unreal.MCPBridgeFuncType.RELOAD:
        instance: Optional[UnrealMCP] = global_context.get_mcp_instance()
        if instance is None:
            return True
        instance.clear_all()
        tool_register.reload_all_tools(instance)
        pass

    if type == unreal.MCPBridgeFuncType.HEARTBEAT_PACKET:
        instance: Optional[UnrealMCP] = global_context.get_mcp_instance()
        return not instance is None
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
