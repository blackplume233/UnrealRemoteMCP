import asyncio
import sys
import importlib

import anyio.to_thread
sys.path.append("Lib/site-packages")


import anyio
import foundation.mcp_app
importlib.reload(foundation.mcp_app)
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp import FastMCP
import unreal
#unreal.log("MCP Initialization Script Loaded")

app = UnrealMCP("Simple-Server",port=8422)
app.run()
