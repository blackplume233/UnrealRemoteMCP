import asyncio
import time
import os
import traceback
from typing import Any, Callable
import uuid
import anyio
import unreal
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings
import uvicorn
import socket

max_tick_count = 86400

class UnrealMCP(FastMCP):
    def __init__(self, name: str | None = None, instructions: str | None = None, **settings: Any):
        super().__init__(name=name, instructions=instructions, **settings)
    
        self.server = None
        self.force_exit = False
        self.tick_count = 0
        self.should_exit = False
        self.uuid = uuid.uuid4()
        self.task_queue = asyncio.Queue()  # 用于存储任务的队列
        #self.tick_loop =  asyncio.SelectorEventLoop()
        

    def sync_run_func(self, function: Any) -> None:
        # 运行函数
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(function())
        pass

    def run(self):
        self.sync_run_func(self.async_run)
        unreal.log("MCP complete run")

    async def async_run(self):
        self.init_bridge()
        # await self.init_server()
        # await self.server.serve()
        try:
            await self.start_up()
        except Exception as e:
            unreal.log_error("Error initializing bridge: " + str(e))
            await self.shutdown()
            return
        
        while not self.should_exit :
            await self.server.on_tick(self.tick_count)
            await asyncio.sleep(1)  # tick在主线程驱动
            #unreal.log("Tick " + str(not self.should_exit))
            
        await self.shutdown()
        
        pass

    def sync_tick(self):
        anyio.run(self.tick)
        pass
         
    def init_bridge(self):
        context = unreal.MCPObject()
        context.bridge = unreal.MCPBridgeFuncDelegate()
        context.bridge.bind_callable(self.on_bridge)
        context.tick = unreal.MCPObjectEventFunction()
        context.tick.bind_callable(self.sync_tick)
        context.guid = str(self.uuid)
        context.python_object_handle = unreal.create_python_object_handle(self)
        unreal.get_editor_subsystem(unreal.MCPSubsystem).setup_object(context)
        unreal.log("Bridge setup " + str(self.uuid))

    def clear_bridge(self):
        unreal.get_editor_subsystem(unreal.MCPSubsystem).clear_object()

    def on_bridge(self, type: unreal.MCPBridgeFuncType, message: str):
        unreal.log("Bridge Message: " + message)
        if type == unreal.MCPBridgeFuncType.EXIT:
            self.should_exit = True
            self.clear_bridge()
        if type == unreal.MCPBridgeFuncType.START:
            pass

    async def init_server(self) -> None:
        """Run the server using SSE transport."""
        starlette_app = self.sse_app()

        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            timeout_graceful_shutdown = 10,
            log_level=self.settings.log_level.lower(),
        )
        self.server = uvicorn.Server(config)

    async def start_up_server(self, server: uvicorn.Server, sockets: list[socket.socket] | None = None) -> None:
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
        #self.init_bridge()
        unreal.log("Server started " + str(self.uuid))

    async def shutdown(self):
        unreal.log("begin stop")
        await self.tick()
        await self.server.shutdown(sockets=None)
        self.clear_bridge()
        unreal.log("Server stopped " + str(self.uuid))

    async def tick(self) -> bool:
        self.tick_count += 1
        self.tick_count = self.tick_count % max_tick_count
        await self.do_task()
        return True
    
    async def do_task(self) -> None:
        # 运行任务
         while not self.task_queue.empty():
            func, args, kwargs,future = await self.task_queue.get()
            try:
                result = func(*args, **kwargs)
                future.set_result(result)
                unreal.log(f"Executed tool: {func.__name__}, Result: {result}")
            except Exception as e:
                unreal.log_error(f"Error executing tool {func.__name__}: {str(e)}")
    async def to_tick_thread(self, func:Callable, *args: Any, **kwargs: Any) -> Any:
        # 将函数添加到任务队列
        unreal.log("Add task to queue")
        future = asyncio.Future()
        await self.task_queue.put((func, args, kwargs, future))
        return await future


