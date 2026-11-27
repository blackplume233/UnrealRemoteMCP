"""Smoke test against a running Unreal Editor's RemoteMCP endpoint."""

import argparse
import asyncio
import json

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def smoke_test(url: str, native: bool) -> None:
    prefix = "remotemcp." if native else ""
    async with (
        httpx.AsyncClient(trust_env=False) as http_client,
        streamable_http_client(url, http_client=http_client) as (read, write, _),
    ):
        async with ClientSession(read, write) as session:
            identity = await session.initialize()
            if native:
                # UE 5.8 source builds may leave the native server name empty.
                assert identity.serverInfo.name in {"", "unreal-mcp"}, identity.serverInfo
            tools = {tool.name: tool for tool in (await session.list_tools()).tools}
            assert tools[prefix + "run_python_script_async"].inputSchema["required"] == ["script"]
            alternate_name = "get_unreal_state" if native else "remotemcp.get_unreal_state"
            assert alternate_name not in tools

            async def call(name: str, **arguments):
                result = await session.call_tool(prefix + name, arguments)
                assert not result.isError, result
                payload = result.structuredContent
                if payload is None:
                    payload = json.loads(result.content[0].text)
                # FastMCP wraps dynamically typed structured results under result.
                if isinstance(payload.get("result"), dict):
                    return payload["result"]
                return payload

            state = await call("get_unreal_state")
            assert state["status"] == "connected", state
            assert state["mcp_server"]["backend"] == ("native" if native else "standalone"), state
            domains = await call("get_dispatch")
            assert "edgraph" in domains["domains"], domains
            reference = await call("call_dispatch_tool", domain="edgraph", tool_name="edgraph_api_reference")
            assert reference["status"] == "success", reference

            assert (await call("run_python_script", script="result = 42"))["result"] == "42"

            script = "\n".join([
                "from foundation.global_context import get_mcp_instance",
                "async def probe():",
                "    await get_mcp_instance().next_frame()",
                "    return 'after_frame'",
                "result = probe()",
            ])
            assert (await call("run_python_script_async", script=script))["result"] == "after_frame"
            invalid = await session.call_tool(prefix + "run_python_script", {"script": "raise ValueError('smoke test')"})
            assert invalid.isError and "smoke test" in invalid.content[0].text, invalid

            if native:
                for command in ("ModelContextProtocol.RefreshTools", "MCP.Reload"):
                    await call("run_console_command", command=command)
                    assert (await call("get_unreal_state"))["status"] == "connected"

                await session.call_tool(prefix + "run_console_command", {"command": "MCP.Restart"})
                names = [tool.name for tool in (await session.list_tools()).tools]
                assert names.count(prefix + "get_unreal_state") == 1, names
                assert (await call("get_unreal_state"))["status"] == "connected"

    print(f"RemoteMCP smoke test passed: {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Streamable HTTP endpoint, including /mcp")
    parser.add_argument("--native", action="store_true", help="Expect the UE 5.8+ Unreal MCP backend")
    args = parser.parse_args()
    asyncio.run(asyncio.wait_for(smoke_test(args.url, args.native), timeout=60))
