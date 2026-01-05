import json
from typing import Any, Callable,Optional

import unreal


class UnrealDelegateProxy:
    def __init__(self, delegate: Callable):
        self.delegate = delegate

    def call(self, in_parameter : unreal.JsonObjectParameter) -> unreal.JsonObjectParameter:
        return self.delegate(in_parameter)
    


def combine_code_path(root: str, plugin_name: str, relative_path: str) -> str:
    """Combine the code path from the specified root, plugin name and relative path.
    The path should be relative to the Project Source directory.
    Arguments:
        root: The root path of the project. It should be "Project" or "Engine".
        plugin_name: Optional, The name of the plugin. if is none, it will be the project name.
        relative_path: The relative path to the file from the Project Source directory.
    """
    source_path : str = "Source"
    base_path : Optional[str] = None
    if plugin_name is None or plugin_name is "":
        base_path = unreal.MCPPythonBridge.plugin_directory(plugin_name)
        base_path = unreal.Paths.combine(base_path, source_path) # type: ignore
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

def str_to_unreal_json(string_data: str) -> unreal.JsonObjectParameter:
    return unreal.MCPJsonUtils.make_json_object(string_data)

def parameter_to_string(json_obj: unreal.JsonObjectParameter) -> str:
    return unreal.MCPJsonUtils.json_object_to_string(json_obj)

def to_py_json(json_obj: unreal.JsonObjectParameter) -> dict:
    return json.loads(parameter_to_string(json_obj))

def call_cpp_tools(function : Callable, params: dict) -> dict:
    # json_params = to_unreal_json(params)
    # return to_py_json(function(json_params))
    str_ret = safe_call_cpp_tools(function, params)
    return json.loads(str_ret)

def safe_call_cpp_tools(function : Callable, params: dict) -> str:
    json_params = json.dumps(params)
    closure  = UnrealDelegateProxy(function)
    delegate = unreal.MCPCommandDelegate()
    delegate.bind_callable(closure.call)
    return unreal.MCPPythonBridge.safe_call_cpp_function(delegate,json_params) # type: ignore
    

def like_str_parameter(params:dict | str, name:str, default_value:Any) -> Any:
    if isinstance(params, dict):
        return params.get(name, default_value)
    elif isinstance(params, str):
        return params
    else:
        raise ValueError("Invalid params type. It should be a dictionary or a string.")


