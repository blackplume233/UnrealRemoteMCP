import asyncio
import inspect
import json

import unreal
from mcp.types import CallToolResult, TextContent

from foundation.mcp_app import UnrealMCP


class NativeUnrealMCP(UnrealMCP):
    """Run RemoteMCP's tools on the editor tick for the engine's MCP server."""

    def __init__(self):
        super().__init__("Remote Unreal MCP", native_backend=True)
        self._calls: dict[str, asyncio.Task] = {}
        self._stopping = False
        self._subsystem = unreal.MCPSubsystem.get()

    def publish_tools(self) -> bool:
        descriptors = [
            {
                "name": f"remotemcp.{tool.name}",
                "description": tool.description,
                "inputSchema": tool.parameters,
                "outputSchema": tool.output_schema,
            }
            for tool in self._tool_manager.list_tools()
        ]
        return self._subsystem.publish_native_tools(json.dumps(descriptors))

    async def to_tick_thread(self, func, *args, **kwargs):
        # Native MCP already dispatches tool calls on the editor's game thread.
        result = func(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result

    def invoke(self, message: str) -> bool:
        if self._stopping:
            return False
        call = json.loads(message)
        call_id = call["id"]
        name = call["name"].removeprefix("remotemcp.")
        task = self._tick_loop.create_task(self.call_tool(name, call["arguments"]))
        self._calls[call_id] = task
        task.add_done_callback(lambda completed: self._complete(call_id, completed))
        return True

    def _complete(self, call_id: str, task: asyncio.Task) -> None:
        self._calls.pop(call_id, None)
        if self._stopping:
            return
        try:
            result = task.result()
            if not isinstance(result, CallToolResult):
                if isinstance(result, tuple):
                    content, structured = result
                    result = CallToolResult(content=content, structuredContent=structured)
                else:
                    result = CallToolResult(content=result)
        except (asyncio.CancelledError, Exception) as error:
            result = CallToolResult(
                content=[TextContent(type="text", text=str(error) or "RemoteMCP tool call cancelled")],
                isError=True,
            )
        self._subsystem.complete_native_tool(call_id, result.model_dump_json(by_alias=True, exclude_none=True))

    def cancel(self, call_id: str) -> None:
        task = self._calls.get(call_id)
        if task is not None:
            task.cancel()

    def reload_all_tools(self):
        if self._tick_loop.is_running():
            self.need_reload = True
            return
        super().reload_all_tools()
        if not self.publish_tools():
            unreal.log_error("Failed to publish reloaded RemoteMCP tools")

    def sync_tick(self):
        super().sync_tick()
        if self._stopping:
            self._close_loop()
        elif self.need_reload:
            self.reload_all_tools()

    def stop(self) -> None:
        self._stopping = True
        for task in self._calls.values():
            task.cancel()
        if not self._tick_loop.is_running():
            self._close_loop()

    def _close_loop(self) -> None:
        if self._calls:
            self._tick_loop.run_until_complete(asyncio.gather(*self._calls.values(), return_exceptions=True))
        self._tick_loop.close()
