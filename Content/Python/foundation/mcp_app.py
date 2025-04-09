import asyncio
import os
from typing import Any
import click
from mcp.server.fastmcp.server import Settings
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.fastmcp import FastMCP
import uvicorn
import socket
import unreal

class UnrealMCP :
    def __init__(self, name: str | None = None, instructions: str | None = None, **settings: Any):
        self.mcp = FastMCP("111")
        self.mcp.settings = Settings(**settings)
        self.server = None
        self.force_exit = False
        
    def run(self):
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)             
        loop.run_until_complete(self.async_run())
        unreal.log("mcp exit")
        
    async def async_run(self):
        # mcp = FastMCP("RemoteUnreal",port=8422)
        # await mcp.run_sse_async()
        self.init_bridge()
        limit_count = 864000
        await self.start_up()
        should_exit = False
        counter = 0
        while not should_exit and not self.force_exit:
            counter += 1
            counter = counter % limit_count
            should_exit = await self.tick(counter)
            await asyncio.sleep(0.1)
        await self.shutdown()
    
    def init_bridge(self):
        context = unreal.MCPContext()
        context.bridge = unreal.MCPBridgeFuncDelegate()
        context.bridge.bind_callable(self.on_bridge)
        context.running = True
        unreal.get_editor_subsystem(unreal.MCPSubsystem).set_context(context)
    
    def clear_bridge(self):
        context = unreal.MCPContext()
        context.bridge = unreal.MCPBridgeFuncDelegate()
        context.running = False
        unreal.get_editor_subsystem(unreal.MCPSubsystem).set_context(context)
        
        
    def on_bridge(self, type:unreal.MCPBridgeFuncType, message:str):
        unreal.log("Bridge Message: " + message)
        if type == unreal.MCPBridgeFuncType.EXIT:
            self.force_exit = True
    
    async def init_server(self) -> None:
        """Run the server using SSE transport."""
        mcp = self.mcp
        starlette_app = mcp.sse_app()
        
        config = uvicorn.Config(
            starlette_app,
            host=mcp.settings.host,
            port=mcp.settings.port,
            log_level=mcp.settings.log_level.lower(),
        )
        self.server = uvicorn.Server(config)
    
    async def start_up_server(self,server:uvicorn.Server , sockets: list[socket.socket] | None = None) -> None:
        process_id = os.getpid()

        config = server.config
        if not config.loaded:
            config.load()

        server.lifespan = config.lifespan_class(config)
        
        message = "Started server process " + str(process_id)
        unreal.log(message)
        
        await server.startup(sockets=sockets)

        
    async def start_up(self) -> None:
        await self.init_server()
        await self.start_up_server(self.server)
        
        
    async def tick(self, count:int) ->bool:
         ret = await self.server.on_tick(count)
         #self.count= (self.count + 1) % 86400
         return ret
     
    async def shutdown(self):
        await self.server.shutdown(sockets=None)
        self.clear_bridge()
        