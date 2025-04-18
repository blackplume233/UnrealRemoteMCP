import sys
import importlib
import unreal
import os

sys.path.append("Lib/site-packages")

from foundation import log_handler
# importlib.reload(log_handler)

#unreal.log("Logging Initialized")

import foundation.mcp_app
# importlib.reload(foundation.mcp_app)
import warnings
from foundation.mcp_app import UnrealMCP
from foundation import global_context
import tools.common_tools as common_register
import tools.resource as resource_register
import tools.edit_tools as edit_register
#unreal.log("MCP Initialization Script Loaded")



global_context.reload_all_modules()
log_handler.setup_logging()
log_handler.setup_logging("uvicorn.error")

# 忽略 Pydantic 的 'model_fields' 警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message="Accessing the 'model_fields' attribute on the instance is deprecated")

setting : unreal.MCPSetting = unreal.get_default_object(unreal.MCPSetting)
#global_context.rebuild_event_loop()

mcp = UnrealMCP("Remote Unreal MCP",port=setting.port)


common_register.register_common_tools(mcp)
resource_register.register_resource(mcp)
edit_register.register_edit_tool(mcp)

mcp.run()

