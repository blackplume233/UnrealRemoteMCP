import asyncio
import logging
import this
import time
import os
import queue
import traceback
from typing import Any, Awaitable, Callable, Sequence, Optional
import uuid

from mcp.server.fastmcp.tools import tool_manager, Tool
from mcp.types import AnyFunction, CallToolResult, EmbeddedResource, ImageContent, TextContent
import json

import unreal
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings
import uvicorn
import socket
from foundation import global_context
from foundation import utility
max_tick_count = 86400

logger = logging.getLogger()

# region agent log (debug mode)
_AGENT_DEBUG_LOG_PATH = os.environ.get(
    "MCP_DEBUG_LOG",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".debug", "mcp_debug.log"),
)
_AGENT_DEBUG_SESSION_ID = "debug-session"

def _agent_dbg_log(*, hypothesisId: str, location: str, message: str, data: dict | None = None, runId: str = "run1") -> None:
    try:
        log_dir = os.path.dirname(_AGENT_DEBUG_LOG_PATH)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        payload = {
            "sessionId": _AGENT_DEBUG_SESSION_ID,
            "runId": runId,
            "hypothesisId": hypothesisId,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with open(_AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# endregion agent log (debug mode)
class UnrealMCP(FastMCP):
    def __init__(self, name: str | None = None, instructions: str | None = None, **settings: Any):
        super().__init__(name=name, instructions=instructions, **settings)
    
        self.server : uvicorn.Server | None = None
        self.force_exit = False
        self.tick_count = 0
        self.should_exit = False
        self.uuid = uuid.uuid4()
        # 任务队列：server loop 线程 -> 游戏线程 tick loop（跨线程），必须用线程安全队列
        # item = (func, args, kwargs, origin_loop, origin_future)
        self.task_queue: "queue.Queue[tuple[Callable, tuple[Any, ...], dict[str, Any], asyncio.AbstractEventLoop, asyncio.Future]]" = queue.Queue()
        # 游戏线程（每帧调用 sync_tick）专用事件循环：必须是“持久化”的，才能让 Awaitable 跨帧推进
        self._tick_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        # 正在执行中的协程任务（跨帧）
        self._inflight_tasks: set[asyncio.Task] = set()
        # 用于 next_frame：在下一帧开始时统一唤醒
        self._next_frame_waiters: list[asyncio.Future] = []
        self._game_thread_tool_set = set[str]()
        self.need_reload = False
        # AI(Claude Opus 4.5): Domain tool 系统 - 按 domain 分组的工具，不加入默认 tools 列表
        # key: domain 名称, value: dict[tool_name, Tool]
        self._domain_tools: dict[str, dict[str, Tool]] = {}
        # 记录 domain tool 是否需要在 game thread 执行
        self._domain_game_thread_tools: set[str] = set()
        # domain 元信息（description 等），用于 get_dispatch 展示
        # key: domain 名称, value: {"description": str}
        self._domain_meta: dict[str, dict[str, Any]] = {}
        # self.stateless_http = True
        #self.json_response = True
        #self.tick_loop =  asyncio.SelectorEventLoop()
        global_context.rebuild_event_loop()

    def sync_run_func(self, function: Any) -> None:
        # 运行函数
        loop = global_context.get_event_loop()
        loop.run_until_complete(function())
        unreal.log("MCP complete run")
        pass

    def init_unreal_mcp(self):
        # self.init_bridge()
        return
        
    def clear_all(self):
        """清除所有已注册的工具、prompt 和 domain 信息，为热重载做准备。"""
        self._prompt_manager._prompts.clear()
        for exit_tool in self._tool_manager.list_tools():
            self._tool_manager.remove_tool(exit_tool.name)
        # 必须同步清理 game_thread 标记，否则热重载后旧标记残留，
        # 导致同名工具的线程调度行为与新注册的 decorator 不一致
        self._game_thread_tool_set.clear()
        self._domain_tools.clear()
        self._domain_game_thread_tools.clear()
        self._domain_meta.clear()

    def reload_all_tools(self):
        """热重载：清除所有工具注册 → 重新加载 Python 模块 → 重新注册全部工具。"""
        unreal.log("reload begin")
        self.need_reload = False
        from tools import tool_register
        self.clear_all()
        tool_register.reload_all_tools(self)
        unreal.log("reload end")



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
            if self.server is not None:  # guard: server 可能在 start_up 异常后为 None
                await self.server.on_tick(self.tick_count)
            await asyncio.sleep(1)
            if self.need_reload:
                self.reload_all_tools()
        await self.shutdown()
        
        pass

    def unreal_run(self):
        self.sync_run_func(self.async_run)

    def sync_tick(self):
        # 关键：不能每帧新建 event loop（anyio.run 会创建/关闭 loop），否则 Awaitable 无法跨帧续跑
        try:
            prev_loop: asyncio.AbstractEventLoop | None = None
            try:
                # 只影响“当前线程”（游戏线程）的默认 loop，不影响 server loop 线程。
                prev_loop = asyncio.get_event_loop()
            except Exception:
                prev_loop = None

            need_swap = (prev_loop is None) or (prev_loop is not self._tick_loop)
            if need_swap:
                asyncio.set_event_loop(self._tick_loop)

            self._tick_loop.run_until_complete(self.tick())

            # 尽量恢复原来的默认 loop，避免影响同线程的其它 asyncio 使用者
            if need_swap and (prev_loop is not None) and (prev_loop is not self._tick_loop):
                asyncio.set_event_loop(prev_loop)
        except Exception as e:
            unreal.log_error(f"sync_tick exception: {str(e)}\n{traceback.format_exc()}")
        return
         
    # def init_bridge(self):
    #     uuid_str : str = str(self.uuid)
    #     context = unreal.MCPObject()
    #     context.bridge = unreal.MCPBridgeFuncDelegate()
    #     context.bridge.bind_callable(self.on_bridge)
    #     context.tick = unreal.MCPObjectEventFunction()
    #     context.tick.bind_callable(self.sync_tick)
    #     context.guid = uuid_str # type: ignore
    #     context.python_object_handle = unreal.create_python_object_handle(self)
    #     unreal.get_editor_subsystem(unreal.MCPSubsystem).setup_object(context) # type: ignore
    #     unreal.log("Bridge setup " + str(self.uuid))

    # def clear_bridge(self):
    #     unreal.get_editor_subsystem(unreal.MCPSubsystem).clear_object() # type: ignore

    def on_bridge(self, type: unreal.MCPBridgeFuncType, message: str):
        """C++ bridge 回调，在游戏线程中执行（非 async 上下文）。
        EXIT 只设标志位，由 async_run 循环检测后 await shutdown()，
        避免在 sync 方法中调用 async 函数导致协程丢失。"""
        unreal.log("Bridge Message: " + message)
        if type == unreal.MCPBridgeFuncType.EXIT:
            self.should_exit = True
        elif type == unreal.MCPBridgeFuncType.START:
            self.sync_run_func(self.async_run)
        elif type == unreal.MCPBridgeFuncType.RELOAD:
            self.need_reload = True
            self.reload_all_tools()

    async def init_server(self) -> None:
        """Run the server using SSE transport."""
        starlette_app = self.streamable_http_app()

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
        assert self.server is not None, "init_server must set self.server"
        await self.start_up_server(self.server)
        unreal.log("Server started " + str(self.uuid))

    async def shutdown(self):
        unreal.log("begin stop")
        await self.tick()
        if self.server is not None:  # guard: start_up 失败时 server 可能未初始化
            self.server.force_exit = True
            self.server.should_exit = True
            await self.server.shutdown(sockets=None)
        unreal.log("Server stopped " + str(self.uuid))

    async def tick(self) -> bool:
        self.tick_count += 1
        self.tick_count = self.tick_count % max_tick_count

        # 唤醒上一帧等待 next_frame() 的协程
        if self._next_frame_waiters:
            waiters = self._next_frame_waiters
            self._next_frame_waiters = []
            for fut in waiters:
                try:
                    if not fut.done():
                        fut.set_result(True)
                except Exception:
                    pass

        await self.do_task()
        return True
    

    
    async def do_task(self) -> Any:
        """
        运行任务队列。

        设计目标：
        - 同步任务：仍然会在当前帧执行完（无法自动切片）
        - Awaitable 任务：不在当前帧 await 到结束，而是创建 asyncio.Task，让它在后续帧继续推进
          （协程需要在合适的位置 `await self.next_frame()` 或 `await asyncio.sleep(0)` 等来让出执行权）
        """
        max_new_tasks_per_tick = 32  # 防止单帧把队列耗尽导致卡顿
        created = 0

        while created < max_new_tasks_per_tick:
            try:
                func, args, kwargs, origin_loop, origin_future = self.task_queue.get_nowait()
            except queue.Empty:
                break
            try:
                tool_function = func(*args, **kwargs)

                # Awaitable：跨帧执行
                if isinstance(tool_function, Awaitable):
                    async def _run_awaitable(
                        coro: Awaitable,
                        func_name: str,
                        origin_loop_ref: asyncio.AbstractEventLoop,
                        origin_future_ref: asyncio.Future,
                    ):
                        try:
                            # 注意：unreal.PythonLogCaptureContext 是“全局捕获”，并发协程会互相串台，
                            # 因此 Awaitable 不在这里包裹 LogCaptureScope。需要捕获时请在协程内部自行控制。
                            result = await coro
                            unreal.log(f"Task executed with result: {func_name} {result} {type(result)}")
                            if not origin_future_ref.done():
                                origin_loop_ref.call_soon_threadsafe(origin_future_ref.set_result, result)
                        except Exception as e:
                            error_info = f"Error executing tool {func_name}: {str(e)} \n{e.args} \n{traceback.format_exc()}"
                            logger.info(error_info)
                            if not origin_future_ref.done():
                                origin_loop_ref.call_soon_threadsafe(
                                    origin_future_ref.set_result,
                                    CallToolResult(
                                        content=[TextContent(type="text", text=error_info)],
                                        isError=True,
                                    ),
                                )

                    task = asyncio.create_task(_run_awaitable(tool_function, func.__name__, origin_loop, origin_future))
                    self._inflight_tasks.add(task)
                    task.add_done_callback(lambda t: self._inflight_tasks.discard(t))
                    created += 1
                    continue

                # 非 Awaitable：当前帧执行
                result = tool_function()  # type: ignore[misc]
                unreal.log(f"Task executed with result: {func.__name__} {result} {type(result)}")
                origin_loop.call_soon_threadsafe(origin_future.set_result, result)
                created += 1

            except Exception as e:
                error_info = f"Error executing tool {func.__name__}: {str(e)} \n{e.args} \n{traceback.format_exc()}"
                logger.info(error_info)
                origin_loop.call_soon_threadsafe(
                    origin_future.set_result,
                    CallToolResult(content=[TextContent(type="text", text=error_info)], isError=True),
                )
                return error_info

        # 给本帧新创建/已就绪的协程一次运行机会（通常会跑到下一个 await 点就让出）
        await asyncio.sleep(0)
        
                
    async def to_tick_thread(self, func:Callable, *args: Any, **kwargs: Any) -> Any:
        # 将函数添加到任务队列（server loop 线程 -> 游戏线程）
        unreal.log("Add task to game thread task queue")
        origin_loop = asyncio.get_running_loop()
        origin_future = origin_loop.create_future()
        self.task_queue.put((func, args, kwargs, origin_loop, origin_future))
        return await origin_future
    
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource] | Any:
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
            return CallToolResult(
                content=[TextContent(type="text", text=info)],
                isError=True,
            )
    
    
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

            # region agent log (debug mode)
            # H1: 热重载没有替换旧工具（ToolManager.add_tool 返回 existing）
            try:
                existed = False
                if hasattr(self, "_tool_manager") and getattr(self, "_tool_manager", None) is not None:
                    existed = self._tool_manager.get_tool(func_name) is not None
                _agent_dbg_log(
                    hypothesisId="H1",
                    location="foundation/mcp_app.py:game_thread_tool",
                    message="register_tool",
                    data={"tool": func_name, "existed_before": existed},
                )
            except Exception:
                pass
            # endregion agent log (debug mode)
            
            #unreal.log(f"Registering tool: {func_name} - {fn_desc}")
            self.add_tool(fn, func_name, fn_desc)
            return fn
            

        return decorator

    # region AI(Claude Opus 4.5): Domain Tool 系统
    def domain_tool(
        self, 
        domain: str, 
        name: str | None = None, 
        description: str | None = None,
        domain_description: str | None = None,
        game_thread: bool = True
    ) -> Callable[[AnyFunction], AnyFunction]:
        """
        装饰器：注册一个 domain tool。
        
        Domain tools 不会加入默认的 MCP tools 列表，而是通过 get_dispatch / dispatch_tool 来访问。
        这样可以减少工具列表噪音，让 AI 按需获取特定领域的工具。
        
        Args:
            domain: 工具所属的领域名称（如 "animation", "material", "landscape" 等）
            name: 工具名称，默认使用函数名
            description: 工具描述，默认使用函数 docstring
            game_thread: 是否在游戏主线程执行，默认 True
            
        用法:
            @mcp.domain_tool("animation")
            def play_animation(actor_name: str, anim_name: str):
                '''播放指定动画'''
                ...
        """
        if callable(domain):
            raise TypeError(
                "The @domain_tool decorator was used incorrectly. "
                "Did you forget to call it? Use @domain_tool('domain_name') instead of @domain_tool"
            )

        def decorator(fn: AnyFunction) -> AnyFunction:
            func_name = name or fn.__name__
            fn_desc = description or fn.__doc__ or ""
            
            # 确保 domain 字典存在
            if domain not in self._domain_tools:
                self._domain_tools[domain] = {}
            if domain not in self._domain_meta:
                self._domain_meta[domain] = {"description": ""}
            # 如调用方提供 domain_description，则写入（允许多次调用覆盖）
            if domain_description is not None:
                self._domain_meta[domain]["description"] = domain_description or ""
            
            # 创建 Tool 对象但不加入 _tool_manager
            tool = Tool.from_function(fn, name=func_name, description=fn_desc)
            self._domain_tools[domain][func_name] = tool
            
            # 记录是否需要 game thread
            if game_thread:
                full_key = f"{domain}:{func_name}"
                self._domain_game_thread_tools.add(full_key)
            
            unreal.log(f"[DomainTool] Registered: {domain}/{func_name}")
            return fn

        return decorator

    def set_domain_description(self, domain: str, description: str) -> None:
        """设置/更新某个 domain 的描述（用于 get_dispatch 展示）。"""
        domain = (domain or "").strip()
        if not domain:
            return
        if domain not in self._domain_meta:
            self._domain_meta[domain] = {"description": ""}
        self._domain_meta[domain]["description"] = description or ""
        # 确保 domain 字典存在，避免只有 meta 没有 tools 时 list_domains_info 漏掉
        if domain not in self._domain_tools:
            self._domain_tools[domain] = {}

    def get_domain_description(self, domain: str) -> str:
        domain = (domain or "").strip()
        if not domain:
            return ""
        try:
            meta = self._domain_meta.get(domain, None)
            if meta:
                return str(meta.get("description", "") or "")
        except Exception:
            pass
        return ""

    def get_domain_tools_info(self, domain: str) -> dict[str, Any]:
        """
        获取指定 domain 下所有工具的信息（用于 get_dispatch）。
        
        Returns:
            {
                "domain": str,
                "tools": [
                    {
                        "name": str,
                        "description": str,
                        "parameters": dict (JSON Schema)
                    },
                    ...
                ]
            }
        """
        if domain not in self._domain_tools:
            return {
                "domain": domain,
                "description": self.get_domain_description(domain),
                "tools": [],
                "error": f"Domain '{domain}' not found. Available domains: {list(self._domain_tools.keys())}"
            }
        
        tools_info = []
        for tool_name, tool in self._domain_tools[domain].items():
            tool_info = {
                "name": tool_name,
                "description": tool.description or "",
                "parameters": tool.parameters,  # JSON Schema
            }
            tools_info.append(tool_info)
        
        return {
            "domain": domain,
            "description": self.get_domain_description(domain),
            "tools": tools_info
        }

    def list_domains(self) -> list[str]:
        """获取所有已注册的 domain 列表"""
        return list(self._domain_tools.keys())

    def list_domains_info(self) -> list[dict[str, Any]]:
        """获取所有 domain 的信息（名称 + 描述）。"""
        out: list[dict[str, Any]] = []
        for d in self.list_domains():
            out.append({"domain": d, "description": self.get_domain_description(d)})
        return out

    def search_domain_tools(self, keyword: str, domain: str = "") -> dict[str, Any]:
        """
        AI(Claude Opus 4.5): 按关键词搜索 domain 工具。
        
        Args:
            keyword: 搜索关键词（在工具名称和描述中匹配，不区分大小写）
            domain: 可选，限定在某个 domain 中搜索；为空则搜索所有 domain
            
        Returns:
            {
                "keyword": str,
                "domain_filter": str,
                "matches": [
                    {
                        "domain": str,
                        "name": str,
                        "description": str,
                        "parameters": dict
                    },
                    ...
                ],
                "total_count": int
            }
        """
        keyword = (keyword or "").strip().lower()
        domain_filter = (domain or "").strip()
        
        if not keyword:
            return {
                "keyword": "",
                "domain_filter": domain_filter,
                "matches": [],
                "total_count": 0,
                "error": "keyword is required"
            }
        
        matches = []
        domains_to_search = [domain_filter] if domain_filter else list(self._domain_tools.keys())
        
        for d in domains_to_search:
            if d not in self._domain_tools:
                continue
            for tool_name, tool in self._domain_tools[d].items():
                # 在名称和描述中搜索
                name_match = keyword in tool_name.lower()
                desc_match = keyword in (tool.description or "").lower()
                
                if name_match or desc_match:
                    matches.append({
                        "domain": d,
                        "name": tool_name,
                        "description": (tool.description or "")[:200],  # 截断过长描述
                        "parameters": tool.parameters
                    })
        
        return {
            "keyword": keyword,
            "domain_filter": domain_filter,
            "matches": matches,
            "total_count": len(matches)
        }

    async def call_domain_tool(self, domain: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        调用指定 domain 下的工具（用于 dispatch_tool）。
        
        Args:
            domain: 工具所属的领域
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if domain not in self._domain_tools:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Domain '{domain}' not found. Available: {list(self._domain_tools.keys())}")],
                isError=True,
            )
        
        if tool_name not in self._domain_tools[domain]:
            available = list(self._domain_tools[domain].keys())
            return CallToolResult(
                content=[TextContent(type="text", text=f"Tool '{tool_name}' not found in domain '{domain}'. Available: {available}")],
                isError=True,
            )
        
        tool = self._domain_tools[domain][tool_name]
        full_key = f"{domain}:{tool_name}"
        
        try:
            # 检查是否需要在 game thread 执行
            if full_key in self._domain_game_thread_tools:
                # 在 game thread 中执行
                async def wrapped_call():
                    return await tool.run(arguments)
                return await self.to_tick_thread(wrapped_call)
            else:
                # 直接执行
                return await tool.run(arguments)
        except Exception as e:
            import traceback
            error_info = f"Error executing domain tool {domain}/{tool_name}: {str(e)}\n{traceback.format_exc()}"
            unreal.log_error(error_info)
            return CallToolResult(
                content=[TextContent(type="text", text=error_info)],
                isError=True,
            )
    # endregion Domain Tool 系统

    async def next_frame(self) -> bool:
        """
        在游戏线程“下一帧”再继续执行（用于把协程工具逐帧切片）。

        用法（在 async tool 里）：
            for i in range(60):
                # ... 做一点点工作 ...
                await global_context.get_mcp_instance().next_frame()
        """
        fut: asyncio.Future = self._tick_loop.create_future()
        self._next_frame_waiters.append(fut)
        return await fut


global_mcp: Optional[UnrealMCP] = None
