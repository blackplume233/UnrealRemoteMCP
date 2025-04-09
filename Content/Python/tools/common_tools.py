
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp.server import FastMCP
import unreal

def register_common_tools(mcp : UnrealMCP):
    @mcp.tool()
    def first_tool():
        return "Hello from first tool!"
    
    @mcp.tool()
    async def tick_get_actor_count(ctx):
        return await mcp.to_tick_thread(get_actor_count,ctx)
    
    def get_actor_count(ctx):
        """Get the number of actors in the current Unreal Engine scene."""
        try:
            # 使用 Unreal 的 ActorIterator 获取所有 Actor
            world = unreal.EditorLevelLibrary.get_editor_world()
            if not world:
                unreal.log_error("Failed to get the current world.")
                return 0
            actor_count = sum(1 for _ in unreal.ActorIterator(world))
            unreal.log(f"Number of actors in the scene: {actor_count}")
            return actor_count
        except Exception as e:
            unreal.log_error(f"Failed to get actor count: {str(e)}")
            return 0
        