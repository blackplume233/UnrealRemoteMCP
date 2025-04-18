
from foundation.mcp_app import UnrealMCP
import foundation.utility as utility
import unreal

def register_resource(mcp:UnrealMCP):
    # @mcp.resource("cpp_code://cpp/{root}/{relative_path}/{plugin_name}")
    # def get_cpp_code(root : str, plugin_name: str, relative_path: str) -> str:
    #     """Get code from the specified path.
    #     The path should be relative to the Project Source directory.
    #     Arguments:
    #         root: The root path of the project. It should be "Project" or "Engine".
    #         plugin_name: Optional, The name of the plugin. if is none, it will be the project name.
    #         relative_path: The relative path to the file from the Project Source directory.
    #     """
    #     try:
    #         unreal.log(f"get_cpp_code: {root}, {plugin_name}, {relative_path}")
    #         path = utility.combine_code_path(root, plugin_name, relative_path)
    #         return path
    #         # with open(path, "r") as file:
    #         #     return file.read()
    #     except FileNotFoundError:
    #         return f"File not found: {path}"
    pass
