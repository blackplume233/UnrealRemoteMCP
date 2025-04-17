
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp.server import FastMCP
import unreal

def register_common_tools(mcp : UnrealMCP):
    @mcp.tool()
    def first_tool():
        return "Hello from first tool!"
    
    @mcp.game_thread_tool()
    def get_actor_count():
        """Get the number of actors in the current Unreal Engine scene."""
        try:
            # 使用 Unreal 的 ActorIterator 获取所有 Actor
            world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            if not world:
                unreal.log_error("Failed to get the current world.")
                return 0
            actor_count = sum(1 for _ in unreal.ActorIterator(world))
            unreal.log(f"Number of actors in the scene: {actor_count}")
            return actor_count
        except Exception as e:
            unreal.log_error(f"Failed to get actor count: {str(e)}")
            return 0
    @mcp.game_thread_tool()
    def run_python_script(script: str):
        """Run a Python script in the Unreal Engine editor.
        Args:
            script (str): The Python script to run. the return of script should can covert to string
        """
        try:
            return str(exec(script))
        except Exception as e:
            #unreal.log_error(f"Failed to execute script: {str(e)}")
            return f"Script execution failed. {str(e)}"

    @mcp.tool()
    def async_run_python_script(script: str):
        """
        Important: This function is not run in the game thread.
        Run a Python script in the Unreal Engine editor.
        Args:
            script (str): The Python script to run. the return of script should can covert to string
        """
        try:
            return str(exec(script))
        except Exception as e:
            #unreal.log_error(f"Failed to execute script: {str(e)}")
            return f"Script execution failed. {str(e)}"
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
        return unreal.MCPPythonBridge.search_console_commands(keyword)
    @mcp.game_thread_tool()
    def run_console_command(command:str):
        """Run a console command in Unreal Engine.
        Args:
            command (str): The console command to run.
        """
        try:
            unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), command)
            return f"Executed console command: {command}"
        except Exception as e:
            unreal.log_error(f"Failed to execute console command: {str(e)}")
            return "Console command execution failed."
        
        pass
    
