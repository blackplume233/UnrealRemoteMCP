import json
import unreal
def combine_code_path(root: str, plugin_name: str, relative_path: str) -> str:
    """Combine the code path from the specified root, plugin name and relative path.
    The path should be relative to the Project Source directory.
    Arguments:
        root: The root path of the project. It should be "Project" or "Engine".
        plugin_name: Optional, The name of the plugin. if is none, it will be the project name.
        relative_path: The relative path to the file from the Project Source directory.
    """
    source_path : str = "Source"
    base_path : str = None
    if plugin_name is None or plugin_name is "":
        base_path = unreal.MCPPythonBridge.PluginDirectory(plugin_name)
        base_path = unreal.Paths.combine(base_path, source_path)
    elif root == "Project":
        base_path= unreal.Paths.game_source_dir()
    elif root == "Engine":
        base_path= unreal.Paths.engine_source_dir()
    else:
        raise ValueError("Invalid root path. It should be 'Project' or 'Plugin'.")
    path = root + "/" + relative_path
    return path

def to_unreal_json(data: dict) -> unreal.JsonObjectParameter:
    string_data = json.dumps(data)
    return unreal.MCPJsonUtils.make_json_object(string_data)

def to_unreal_json(string_data: str) -> unreal.JsonObjectParameter:
    return unreal.MCPJsonUtils.make_json_object(string_data)

def to_string(json_obj: unreal.JsonObjectParameter) -> str:
    return unreal.MCPJsonUtils.json_object_to_string(json_obj)

def to_py_json(json_obj: unreal.JsonObjectParameter) -> dict:
    return json.loads(to_string(json_obj))


