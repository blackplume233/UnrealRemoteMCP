
import asyncio
from asyncio.windows_events import NULL
import time
from typing import Any, Awaitable, Dict, List, Optional
from foundation.log_handler import LogCaptureScope
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp.server import FastMCP
from mcp.types import CallToolResult, TextContent
import unreal
from foundation.utility import like_str_parameter


def _resolve_world_context() -> Dict[str, Any]:
    editor_subsystem = None
    level_subsystem = None
    game_world = None
    editor_world = None
    is_in_pie = False

    try:
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    except Exception:
        editor_subsystem = None

    try:
        level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if level_subsystem:
            is_in_pie = bool(level_subsystem.is_in_play_in_editor())
    except Exception:
        level_subsystem = None

    if editor_subsystem:
        try:
            game_world = editor_subsystem.get_game_world()
        except Exception:
            game_world = None
        try:
            editor_world = editor_subsystem.get_editor_world()
        except Exception:
            editor_world = None

    world = game_world or editor_world
    world_source = "game" if game_world else "editor" if editor_world else "none"

    return {
        "world": world,
        "game_world": game_world,
        "editor_world": editor_world,
        "world_source": world_source,
        "is_in_pie": is_in_pie,
    }


def _describe_world(world_context: Dict[str, Any]) -> Dict[str, Any]:
    world = world_context["world"]
    current_level = None
    actor_count = 0
    world_name = None
    world_type = None

    if world:
        try:
            world_name = world.get_name()
        except Exception:
            world_name = None

        try:
            world_type = str(world.world_type)
        except Exception:
            world_type = None

        try:
            current_level = unreal.GameplayStatics.get_current_level_name(world, True)
        except Exception:
            if world_context["world_source"] == "editor":
                try:
                    current_level = unreal.EditorLevelLibrary.get_current_level_name(world)
                except Exception:
                    current_level = world_name
            else:
                current_level = world_name

        try:
            all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
            actor_count = len(all_actors) if all_actors else 0
        except Exception:
            if world_context["world_source"] == "editor":
                try:
                    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
                    actor_count = len(all_actors) if all_actors else 0
                except Exception:
                    actor_count = 0

    return {
        "current_level": current_level or "unknown",
        "actor_count": actor_count,
        "world_name": world_name,
        "world_type": world_type,
    }


def register_common_tools(mcp : UnrealMCP):
    @mcp.game_thread_tool()
    def run_python_script(script: str):
        """Run a Python script in the Unreal Engine editor，the result must is str.
        Args:
            script (str): The Python script to run. the return of script should can covert to string, if except return any value ,you need save it in var 
        """
        try:
            # script = like_str_parameter(script, "script", "")
            with LogCaptureScope() as log_capture:
                namespace = {}
                exec(script,namespace)
                namespace.pop('__builtins__')
                ret = f"{namespace.get('result',namespace)}"
                logs = f"{log_capture.get_logs()}"
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"result: {ret}\nlogs:\n{logs}",
                        )
                    ],
                    structuredContent={
                        "result": ret,
                        "logs": logs,
                    },
                )
        except Exception as e:
            #unreal.log_error(f"Failed to execute script: {str(e)}")
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text=f"Script execution failed. {str(e)}")],
            )

    @mcp.game_thread_tool(
        "run_python_script_async",
        description="在主线程里分帧执行给定的Python脚本；如果 result 是 awaitable 会 await（默认 await 阶段不捕获日志，避免长任务期间 UE 日志不显示/看起来卡住）",
    )
    async def run_python_script_async(script: str):
        """
        在主线程里分帧执行Python脚本。如果 result 是 awaitable 对象则等待其完成。分支执行期间不要使用unreal.ScopedSlowTask，避免卡住主线程。

        Args:
            script (str): 需要在Unreal主线程中执行的Python脚本内容。
        Returns:
            CallToolResult: 包含result和日志字符串
        """
        try:
            # 说明：
            # - unreal.PythonLogCaptureContext 是"全局捕获"，一旦 begin_capture，UE Output Log 往往不会实时显示。
            # - 对于长时间 await（逐帧 next_frame）场景，长期占用捕获会让用户感觉"主线程卡住/没日志/SlowTask 不关"。
            # 因此：只在 exec 阶段捕获；await 阶段默认不捕获（可用参数回退旧行为）。

            logs_pre = ""
            namespace = {}
            with LogCaptureScope() as log_capture:
                exec(script, namespace)
                namespace.pop("__builtins__", None)
                result = namespace.get("result", namespace)
                logs_pre = f"{log_capture.get_logs()}"

            is_awaitable = hasattr(result, "__await__") and isinstance(result, Awaitable)

            # await 阶段：默认不捕获日志（让 unreal.log 实时输出）
            logs_post = ""
            if is_awaitable:
                try:
                    with LogCaptureScope() as log_capture2:
                        result = await result  # type: ignore[misc]  # 运行时已由 is_awaitable guard 确保可 await
                        logs_post = f"{log_capture2.get_logs()}"
                except Exception as await_exc:
                    logs = logs_pre + logs_post
                    return CallToolResult(
                        isError=True,
                        content=[TextContent(type="text", text=f"Await result failed: {str(await_exc)}\nlogs:\n{logs}")],
                        structuredContent={"result": f"{await_exc}", "logs": logs},
                    )

            ret_str = f"{result}"
            logs = logs_pre + logs_post
            return CallToolResult(
                content=[TextContent(type="text", text=f"result: {ret_str}\nlogs:\n{logs}")],
                structuredContent={"result": ret_str, "logs": logs},
            )
        except Exception as e:
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text=f"Async script execution failed. {str(e)}")],
            )

    @mcp.game_thread_tool()
    def search_console_commands(keyword: str):
        """Search the console commands by a specific keyword.
        Args:
            keyword (str): The keyword to search for in console commands.
        Returns:
            {
                ConsoleObjects:
                [
                    {
                        Key:word: str,  # The keyword used to search for commands.
                        Help: str,  # The help text for the command.
                    }
                    
                ] :str # The help text for the command.
            }
        """
        keyword = like_str_parameter(keyword, "keyword", "")
        if keyword is None or keyword.isspace() :
            return 'key word is empty'
        return unreal.MCPPythonBridge.search_console_commands(keyword)

    @mcp.game_thread_tool()
    def run_console_command(command:str):
        """Run a console command in Unreal Engine.
        Args:
            command (str): The console command to run.
        """
        try:
            unreal.log(command)
            command = like_str_parameter(command, "command", "")
            with LogCaptureScope() as log_capture:
                editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
                if editor_subsystem is None:  # PIE 未启动或 subsystem 被回收时可能为 None
                    return CallToolResult(isError=True, content=[TextContent(type="text", text="EditorSubsystem not available")])
                world  : Optional[unreal.World] = editor_subsystem.get_game_world()
                if world is NULL:
                    world = editor_subsystem.get_editor_world()
                    
                if world is NULL:
                    unreal.log("not exit world")
                    return
                unreal.SystemLibrary.execute_console_command(world, command) # type: ignore
                logs = f"{log_capture.get_logs()}"
                return CallToolResult(
                    content=[TextContent(type="text", text=f"success\nlogs:\n{logs}")],
                    structuredContent={
                        "result": "success",
                        "logs": logs,
                    },
                )
            return CallToolResult(isError=True, content=[TextContent(type="text", text="Unknown error")])
        except Exception as e:
            unreal.log_error(f"Failed to execute console command: {str(e)}")
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text=f"Console command execution failed. {str(e)}")],
            )
        
        pass

    @mcp.game_thread_tool()
    def get_unreal_state() -> Dict[str, Any]:
        """获取 Unreal Engine 环境与连接状态的综合信息。

        一次调用返回项目路径、源码目录、引擎目录、日志目录、API stub 路径、
        当前关卡、Actor 数量、Python 运行时信息、MCP 服务端口等。

        Returns:
            Dict containing:
            - status: "connected" | "error"
            - paths.project_dir, paths.source_dirs, paths.engine_dir, paths.log_dir, paths.unreal_api
            - current_level, actor_count
            - engine_info.editor_world_available
            - python_info.version, python_info.platform
            - mcp_server.port, mcp_server.status
        """
        try:
            import sys
            import platform

            project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

            # paths
            source_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.game_source_dir())
            script_dir = unreal.Paths.combine([source_dir, "..", "Script"])  # type: ignore[arg-type]
            engine_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir())
            log_dir = unreal.Paths.combine([project_dir, "Saved", "Logs"])  # type: ignore[arg-type]

            unreal_api_path = unreal.Paths.combine([project_dir, "Intermediate", "PythonStub", "unreal.py"])  # type: ignore[arg-type]
            if not unreal.Paths.file_exists(unreal_api_path):
                unreal_api_path = None

            # level info
            world_context = _resolve_world_context()
            world_info = {
                "current_level": "unknown",
                "actor_count": 0,
                "world_name": None,
                "world_type": None,
            }
            try:
                world_info = _describe_world(world_context)
            except Exception as e:
                unreal.log_warning(f"获取关卡信息时出错: {str(e)}")

            # MCP settings
            mcp_port = None
            try:
                setting = unreal.get_default_object(unreal.MCPSetting)
                if setting:
                    mcp_port = setting.port
            except Exception as e:
                unreal.log_warning(f"获取 MCP 设置时出错: {str(e)}")

            return {
                "status": "connected",
                "paths": {
                    "project_dir": project_dir,
                    "source_dirs": [source_dir, script_dir],
                    "engine_dir": engine_dir,
                    "log_dir": log_dir,
                    "unreal_api": unreal_api_path,
                },
                "current_level": world_info["current_level"],
                "actor_count": world_info["actor_count"],
                "engine_info": {
                    "editor_world_available": world_context["editor_world"] is not None,
                    "game_world_available": world_context["game_world"] is not None,
                    "is_in_play_in_editor": world_context["is_in_pie"],
                    "world_source": world_context["world_source"],
                    "world_name": world_info["world_name"],
                    "world_type": world_info["world_type"],
                },
                "python_info": {
                    "version": sys.version,
                    "version_info": {
                        "major": sys.version_info.major,
                        "minor": sys.version_info.minor,
                        "micro": sys.version_info.micro,
                    },
                    "platform": platform.platform(),
                    "executable": sys.executable,
                },
                "mcp_server": {
                    "port": mcp_port,
                    "status": "running" if mcp_port else "unknown",
                },
            }

        except Exception as e:
            unreal.log_error(f"获取引擎状态时出错: {str(e)}")
            import traceback
            unreal.log_error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    @mcp.game_thread_tool()
    def reload_all_tool():
        """热重载所有的tools"""
        run_console_command("mcp.reload")
        return "reload all tool"

    # region AI(Claude Opus 4.5): Domain Tool 调度接口
    @mcp.tool()
    def search_domain_tools(keyword: str, domain: str = "") -> Dict[str, Any]:
        """
        按关键词搜索 domain 工具。
        
        在所有（或指定）domain 中搜索工具名称和描述包含关键词的工具。
        
        Args:
            keyword: 搜索关键词（不区分大小写）
            domain: 可选，限定在某个 domain 中搜索；为空则搜索所有 domain
            
        Returns:
            匹配的工具列表，包含 domain、名称、描述和参数定义
        """
        return mcp.search_domain_tools(keyword, domain)

    @mcp.tool()
    def get_dispatch(domain: str = "") -> Dict[str, Any]:
        """
        获取指定 domain 下的所有可用工具信息。
        
        Domain tools 是按领域分组的工具，不在默认工具列表中显示。
        使用此工具发现特定领域的工具，然后通过 dispatch_tool 调用它们。
        
        Args:
            domain: 领域名称。如果为空，返回所有可用的 domain 列表。
            
        Returns:
            如果 domain 为空：返回 {"domains": [...]} 所有可用领域列表
            如果指定 domain：返回该领域下所有工具的详细信息，包括名称、描述和参数定义
        """
        if not domain or domain.strip() == "":
            domains = mcp.list_domains()
            return {
                "domains": domains,
                "domains_info": mcp.list_domains_info(),
                "hint": "Use get_dispatch(domain='<domain_name>') to get tools in a specific domain"
            }
        return mcp.get_domain_tools_info(domain.strip())

    @mcp.tool()
    async def call_dispatch_tool(domain: str, tool_name: str, arguments: dict | None = None) -> Any:
        """
        调用指定 domain 下的工具。
        
        先使用 get_dispatch 获取 domain 下的工具信息，了解可用工具及其参数，
        然后使用此工具执行具体的 domain tool。
        
        Args:
            domain: 工具所属的领域名称
            tool_name: 要调用的工具名称
            arguments: 工具参数 dict
            
        Returns:
            工具执行结果
        """
        return await mcp.call_domain_tool(domain, tool_name, arguments or {})
    # endregion Domain Tool 调度接口
