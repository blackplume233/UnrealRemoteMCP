
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


def register_common_tools(mcp : UnrealMCP):
    @mcp.game_thread_tool()
    def test_tool():
        with LogCaptureScope() as log_capture:
            unreal.log_error(f"Executed tool: test_tool")
        return "Hello from first tool!" + f"{log_capture.get_logs()}"

    @mcp.game_thread_tool()
    async def test_tool_async(steps: int = 10, wait_frames: int = 1):
        """
        用于验证：game_thread 的 async tool 是否能“逐帧”推进。

        - steps: 打印次数
        - wait_frames: 每次打印后等待的帧数（>=1 推荐）
        """
        with LogCaptureScope() as log_capture:
            steps = int(steps) if steps is not None else 10
            wait_frames = int(wait_frames) if wait_frames is not None else 1
            if steps <= 0:
                return {"result": "skipped", "reason": "steps<=0"}
            if wait_frames <= 0:
                wait_frames = 1

            unreal.log(f"test_tool_async start: steps={steps}, wait_frames={wait_frames}")
            for i in range(steps):
                unreal.log(f"test_tool_async step {i+1}/{steps} (tick={getattr(mcp, 'tick_count', None)})")
                for _ in range(wait_frames):
                    await mcp.next_frame()
            unreal.log("test_tool_async end")
            return {"result": "ok", "steps": steps, "wait_frames": wait_frames, "logs": f"{log_capture.get_logs_string()}"}


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
            # - unreal.PythonLogCaptureContext 是“全局捕获”，一旦 begin_capture，UE Output Log 往往不会实时显示。
            # - 对于长时间 await（逐帧 next_frame）场景，长期占用捕获会让用户感觉“主线程卡住/没日志/SlowTask 不关”。
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
                        result = await result
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
                editor_subsystem : unreal.UnrealEditorSubsystem  = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
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
    def get_unreal_api( ) : 
        """get a file path  include all unreal api"""
        try:
            # 获取项目根目录
            project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
            # 组合 unrealpy 路径
            unreal_py_api_path = unreal.Paths.combine([project_dir, "Intermediate", "PythonStub", "unreal.py"])
            # 检查目录是否存在
            
            if unreal.Paths.file_exists(unreal_py_api_path):
                return unreal_py_api_path
            else:
                return f"unrealpy 目录不存在: {unreal_py_api_path}"
        except Exception as e:
            return f"获取 unrealpy 目录时出错: {str(e)}"
    
    @mcp.game_thread_tool()
    def get_project_dir() -> str:
        """
        获取Unreal项目的根目录路径

        Returns:
            str: 项目根目录的完整路径
        """
        try:
            return unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
        except Exception as e:
            return f"获取项目目录失败: {str(e)}"

    @mcp.game_thread_tool()
    def get_source_dir() -> str:
        """
        获取Unreal项目源码目录路径

        Returns:
            str: 源码目录的完整路径
        """
        try:
            # 获取项目源码目录（通常为 Source 目录）
            source_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.game_source_dir())
            script_dir = unreal.Paths.combine([source_dir,"..","Script"])
            return str([source_dir, script_dir])
        except Exception as e:
            return f"获取源码目录失败: {str(e)}"

    @mcp.game_thread_tool()
    def get_engine_dir() -> str:
        """
        获取Unreal Engine目录路径
        """
        try:
            return unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir())
        except Exception as e:
            return f"获取Engine目录失败: {str(e)}"
    
    @mcp.game_thread_tool()
    def get_log_dir()->str:
        """获取当前引擎log输出的目录，其中<项目名称>.log是当前的log文件"""
        try:
            # 获取项目根目录
            project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
            # 组合 unrealpy 路径
            unreal_py_api_path = unreal.Paths.combine([project_dir, "Saved", "Logs"])
            # 检查目录是否存在
            
            return unreal_py_api_path
        except Exception as e:
            return f"获取 unrealpy 目录时出错: {str(e)}"


    @mcp.game_thread_tool()
    def test_engine_state() -> Dict[str, Any]:
        """测试连接状态，返回详细的引擎和连接信息
        
        Returns:
            包含以下信息的字典:
            - status: 连接状态 ("connected" 或 "disconnected")
            - engine_version: Unreal Engine 版本信息
            - current_level: 当前关卡名称
            - actor_count: 当前关卡中的 Actor 数量
            - python_version: Python 版本信息
            - mcp_server_status: MCP 服务器状态
        """
        try:
            import sys
            import platform
            
            # 获取当前关卡信息
            current_level = None
            actor_count = 0
            try:
                world = unreal.EditorLevelLibrary.get_editor_world()
                if world:
                    # UE Python API 这里需要传入 world_context_object
                    # （不同版本可能没有无参重载）
                    try:
                        current_level = unreal.EditorLevelLibrary.get_current_level_name(world)
                    except Exception:
                        current_level = world.get_name()
                    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
                    actor_count = len(all_actors) if all_actors else 0
            except Exception as e:
                unreal.log_warning(f"获取关卡信息时出错: {str(e)}")
            
            # 获取 MCP 设置
            mcp_port = None
            try:
                setting = unreal.get_default_object(unreal.MCPSetting)
                if setting:
                    mcp_port = setting.port
            except Exception as e:
                unreal.log_warning(f"获取 MCP 设置时出错: {str(e)}")
            
            # 构建状态信息
            status_info = {
                "status": "connected",
                "engine_info": {
                    "python_available": True,
                    "editor_world_available": world is not None if 'world' in locals() else False,
                },
                "current_level": current_level or "未知",
                "actor_count": actor_count,
                "python_info": {
                    "version": sys.version,
                    "version_info": {
                        "major": sys.version_info.major,
                        "minor": sys.version_info.minor,
                        "micro": sys.version_info.micro
                    },
                    "platform": platform.platform(),
                    "executable": sys.executable
                },
                "mcp_server": {
                    "port": mcp_port,
                    "status": "running" if mcp_port else "unknown"
                },
            }
            
            return status_info
            
        except Exception as e:
            unreal.log_error(f"测试引擎状态时出错: {str(e)}")
            import traceback
            unreal.log_error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
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

    
