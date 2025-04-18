from typing import Any, Dict, List
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp import Context
import unreal
import foundation.utility as unreal_utility
def register_edit_tool( mcp:UnrealMCP):
    """Register editor tools with the MCP server."""
    @mcp.game_thread_tool()
    def get_actors_in_level(ctx: Context) -> List[Dict[str, Any]]:
        """Get a list of all actors in the current level."""
        unreal.log("get_actors_in_level")
        all_actors = unreal.MCPEditorTools.handle_get_actors_in_level(unreal_utility.to_unreal_json({}))
        return unreal_utility.to_string(all_actors)
    
    @mcp.game_thread_tool()
    def find_actors_by_name(ctx: Context, pattern: str) -> List[str]:
        """Find actors by name pattern."""
        param = {"pattern": pattern}
        all_actors = unreal.MCPEditorTools.handle_get_actors_in_level()
        return unreal_utility.to_string(all_actors)
        
    
    @mcp.game_thread_tool()
    def spawn_actor(
        ctx: Context,
        name: str,
        type: str,
        location: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = [0.0, 0.0, 0.0]
    ) -> Dict[str, Any]:
        """Create a new actor in the current level.
        
        Args:
            ctx: The MCP context
            name: The name to give the new actor (must be unique)
            type: The type of actor to create (e.g. StaticMeshActor, PointLight)
            location: The [x, y, z] world location to spawn at
            rotation: The [pitch, yaw, roll] rotation in degrees
            
        Returns:
            Dict 
        """
        params = {
                    "name": name,
                    "type": type.upper(),  # Make sure type is uppercase
                    "location": location,
                    "rotation": rotation
        }
        return unreal_utility.to_string(unreal.MCPEditorTools.handle_spawn_actor(params))
    pass

