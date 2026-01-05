
import time
from typing import Dict, List, Optional
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp.server import FastMCP
import unreal
from foundation.utility import like_str_parameter

ue_log_capture = unreal.PythonLogCaptureContext()

class LogCaptureScope:
    def __enter__(self):
        ue_log_capture.clear()
        ue_log_capture.begin_capture()
        return ue_log_capture
    def __exit__(self, exc_type: Optional[type], exc_value: Optional[BaseException], traceback: Optional[object]) -> bool:
        ue_log_capture.end()
        # Do not suppress exceptions
        return False

def register_common_tools(mcp : UnrealMCP):
    @mcp.tool()
    def test_tool():
        return "Hello from first tool!"
    

    @mcp.game_thread_tool()
    def run_python_script(script: str):
        """Run a Python script in the Unreal Engine editor.
        Args:
            script (str): The Python script to run. the return of script should can covert to string, if except return any value ,you need save it in var 
        """
        try:
            # script = like_str_parameter(script, "script", "")
            namespace = {}
            exec(script,namespace)
            namespace.pop('__builtins__')
            ret = namespace.get('result',namespace)
            #unreal.log('execute python' + ret + namespace)
            return ret
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
            script = like_str_parameter(script, "script", "")
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
            unreal.log(command)
            with LogCaptureScope() as log_capture:
                editor_subsystem : unreal.UnrealEditorSubsystem  = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
                unreal.SystemLibrary.execute_console_command(editor_subsystem.get_game_world(), command)
            return f"Executed console command: {command}/ {log_capture.get_logs()} "
        except Exception as e:
            unreal.log_error(f"Failed to execute console command: {str(e)}")
            return f"Console command execution failed. {str(e)}"
        
        pass
    
