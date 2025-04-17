from typing import Any, Dict, List
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp import Context
import unreal
def register_edit_tool( mcp:UnrealMCP):
    """Register editor tools with the MCP server."""
    @mcp.game_thread_tool()
    def get_actors_in_level(ctx: Context) -> List[Dict[str, Any]]:
        """Get a list of all actors in the current level."""
        all_actors = unreal.MCPEditorTools.handle_get_actors_in_level()
        return [actor.to_dict() for actor in all_actors]
    pass

