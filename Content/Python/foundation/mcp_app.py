import asyncio
import logging
import time
import os
import traceback
from typing import Any, Awaitable, Callable, Sequence
import uuid
import anyio
from mcp.types import AnyFunction, EmbeddedResource, ImageContent, TextContent
import unreal
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings
import uvicorn
import socket
from foundation import global_context
max_tick_count = 86400

logger = logging.getLogger()
class UnrealMCP(FastMCP):
    

    def __init__(self, name: str | None = None, instructions: str | None = None, **settings: Any):
        super().__init__(name=name, instructions=instructions, **settings)
    
        self.server = None
        self.force_exit = False
        self.tick_count = 0
        self.should_exit = False
        self.uuid = uuid.uuid4()
        self.task_queue = asyncio.Queue()  # 用于存储任务的队列
        self._game_thread_tool_set = set[str]()
        #self.tick_loop =  asyncio.SelectorEventLoop()
        

    def sync_run_func(self, function: Any) -> None:
        # 运行函数
        loop = global_context.get_event_loop()
        loop.run_until_complete(function())
        unreal.log("MCP complete run")
        pass

    def run(self):
        self.init_bridge()
        

    async def async_run(self):
        # self.init_bridge()
        # await self.init_server()
        # await self.server._serve()
        
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
            self.sync_run_func(self.async_run)()
            pass

    async def init_server(self) -> None:
        """Run the server using SSE transport."""
        starlette_app = self.sse_app()

        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            #timeout_graceful_shutdown = 10,
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
        self.server.force_exit = True
        await self.server.shutdown(sockets=None)
        # self.clear_bridge()
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
                if isinstance(result, Awaitable):
                    result = await result
                future.set_result(result)
                unreal.log(f"Executed tool: {func.__name__}, Result: {result}")
            except Exception as e:
                error_info = f"Error executing tool {func.__name__}: {str(e)}"
                logger.info(error_info)
                future.set_result(error_info)
                return error_info
                
    async def to_tick_thread(self, func:Callable, *args: Any, **kwargs: Any) -> Any:
        # 将函数添加到任务队列
        unreal.log("Add task to game thread task queue")
        future = asyncio.Future()
        await self.task_queue.put((func, args, kwargs, future))
        return await future
    
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool by name with arguments."""
        try:
            unreal.log(f"call_tool  {name} {arguments}" )
            if(self._game_thread_tool_set.__contains__(name)):
                # 在闭包外获取父类方法的引用
                parent_call_tool = FastMCP.call_tool
                # 使用闭包捕获所需的参数和方法
                async def wrapped_call_tool(self_ref=self, name_ref=name, args_ref=arguments, parent_method=parent_call_tool):
                    return await parent_method(self_ref, name_ref, args_ref)
                return await self.to_tick_thread(wrapped_call_tool)
            return await super().call_tool(name, arguments)
        except Exception as e:
            info = f"Error calling tool {name}: {str(e)}"
            unreal.log_error(info)
            return info
    
    
    def game_thread_tool(
        self, name: str | None = None, description: str | None = None
    ) -> Callable[[AnyFunction], AnyFunction]:
        """Decorator to register a tool."""

        # Check if user passed function directly instead of calling decorator
        if callable(name):
            raise TypeError(
                "The @tool decorator was used incorrectly. "
                "Did you forget to call it? Use @tool() instead of @tool"
            )

        def decorator(fn: AnyFunction) -> AnyFunction:
            fn_desc = f'(GameThread){description or fn.__doc__}' 
            func_name =  name or fn.__name__
            self._game_thread_tool_set.add(func_name)
            
            #unreal.log(f"Registering tool: {func_name} - {fn_desc}")
            self.add_tool(fn, func_name, fn_desc)
            return fn
            

        return decorator


global_mcp:UnrealMCP = None
