import sys
import importlib
import unreal
import os

# sys.path.append("Lib/site-packages")

from foundation import log_handler
# importlib.reload(log_handler)

#unreal.log("Logging Initialized")

# import foundation.mcp_app
# importlib.reload(foundation.mcp_app)
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
#unreal.log("MCP Initialization Script Loaded")



global_context.reload_all_modules()

if global_context.get_counter() == 0:
    log_handler.setup_logging()
    log_handler.setup_logging("uvicorn.error")

global_context.increment_counter()

# 忽略 Pydantic 的 'model_fields' 警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message="Accessing the 'model_fields' attribute on the instance is deprecated")

def init_mcp() -> UnrealMCP:
    setting : unreal.MCPSetting = unreal.get_default_object(unreal.MCPSetting)
    #global_context.rebuild_event_loop()

    mcp = UnrealMCP("Remote Unreal MCP", host="0.0.0.0", port=setting.port)


    common_register.register_common_tools(mcp)
    resource_register.register_resource(mcp)
    edit_register.register_edit_tool(mcp)

    unreal.log(f"Unreal MCP Initialized {mcp.uuid}")
    mcp.init_unreal_mcp()
    return mcp

mcp_instance = init_mcp()

