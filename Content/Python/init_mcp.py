import sys
import importlib
import unreal

sys.path.append("Lib/site-packages")

from foundation import log_handler
importlib.reload(log_handler)
log_handler.setup_logging()
log_handler.setup_logging("uvicorn.error")
#unreal.log("Logging Initialized")

import foundation.mcp_app
importlib.reload(foundation.mcp_app)
import warnings
from foundation.mcp_app import UnrealMCP
from foundation import global_context
import tools.common_tools as common_register

#unreal.log("MCP Initialization Script Loaded")

# 忽略 Pydantic 的 'model_fields' 警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message="Accessing the 'model_fields' attribute on the instance is deprecated")

#global_context.rebuild_event_loop()
mcp = UnrealMCP("Remote Unreal MCP",port=8422)

importlib.reload(common_register)
common_register.register_common_tools(mcp)

mcp.run()

