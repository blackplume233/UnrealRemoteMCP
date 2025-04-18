"""
Unreal Python 执行工具

此模块提供在Unreal编辑器中直接执行Python脚本的功能，无需通过MCP连接。
"""

import logging
from typing import Dict, List, Any, Optional, Union
import unreal
import json

# 获取日志记录器
logger = logging.getLogger("UnrealPythonTools")

class UnrealPythonTools:
    """Unreal引擎Python执行工具类"""
    
    @staticmethod
    def execute_python(script: str) -> Any:
        """
        在Unreal编辑器中执行Python脚本
        
        Args:
            script: 要执行的Python脚本字符串
            
        Returns:
            脚本的执行结果
        """
        try:
            # 直接在编辑器中执行Python脚本
            result = eval(script)
            return result
        except Exception as e:
            logger.error(f"执行Python脚本时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_all_actors():
        """获取当前关卡中的所有Actor"""
        try:
            # 使用Unreal Python API获取所有Actor
            world = unreal.EditorLevelLibrary.get_editor_world()
            all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
            
            actors_info = []
            for actor in all_actors:
                actor_info = {
                    "name": actor.get_name(),
                    "class": actor.get_class().get_name(),
                    "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
                    "rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
                    "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z]
                }
                actors_info.append(actor_info)
            
            return actors_info
        except Exception as e:
            logger.error(f"获取Actor列表时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def find_actor_by_name(name_pattern: str):
        """
        按名称模式查找Actor
        
        Args:
            name_pattern: 名称模式（可包含通配符 * 和 ?）
            
        Returns:
            匹配的Actor列表
        """
        try:
            all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
            matched_actors = []
            
            import fnmatch
            for actor in all_actors:
                actor_name = actor.get_name()
                if fnmatch.fnmatch(actor_name, name_pattern):
                    actor_info = {
                        "name": actor_name,
                        "class": actor.get_class().get_name(),
                        "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
                        "rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
                        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z]
                    }
                    matched_actors.append(actor_info)
            
            return matched_actors
        except Exception as e:
            logger.error(f"查找Actor时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def create_actor(actor_class: str, actor_name: str, location: List[float], rotation: List[float], scale: List[float] = None):
        """
        在场景中创建一个新的Actor
        
        Args:
            actor_class: Actor类名
            actor_name: 新Actor的名称
            location: [x, y, z] 位置
            rotation: [pitch, yaw, roll] 旋转
            scale: [x, y, z] 缩放（可选）
            
        Returns:
            创建的Actor信息
        """
        try:
            # 解析位置和旋转
            location_vector = unreal.Vector(location[0], location[1], location[2])
            rotation_rotator = unreal.Rotator(rotation[0], rotation[1], rotation[2])
            
            # 获取指定的类
            actor_class_obj = unreal.find_class(actor_class)
            if not actor_class_obj:
                return {"error": f"找不到指定的Actor类: {actor_class}"}
            
            # 创建Actor
            world = unreal.EditorLevelLibrary.get_editor_world()
            new_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                actor_class_obj, 
                location_vector, 
                rotation_rotator
            )
            
            # 重命名Actor
            new_actor.rename(actor_name)
            
            # 设置缩放（如果提供）
            if scale:
                new_actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
            
            # 返回创建的Actor信息
            actor_info = {
                "name": new_actor.get_name(),
                "class": new_actor.get_class().get_name(),
                "location": [new_actor.get_actor_location().x, new_actor.get_actor_location().y, new_actor.get_actor_location().z],
                "rotation": [new_actor.get_actor_rotation().pitch, new_actor.get_actor_rotation().yaw, new_actor.get_actor_rotation().roll],
                "scale": [new_actor.get_actor_scale3d().x, new_actor.get_actor_scale3d().y, new_actor.get_actor_scale3d().z]
            }
            
            return actor_info
        except Exception as e:
            logger.error(f"创建Actor时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def delete_actor(actor_name: str):
        """
        从场景中删除指定的Actor
        
        Args:
            actor_name: 要删除的Actor名称
            
        Returns:
            操作结果
        """
        try:
            all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
            
            for actor in all_actors:
                if actor.get_name() == actor_name:
                    unreal.EditorLevelLibrary.destroy_actor(actor)
                    return {"success": True, "message": f"已成功删除Actor: {actor_name}"}
            
            return {"success": False, "message": f"找不到指定的Actor: {actor_name}"}
        except Exception as e:
            logger.error(f"删除Actor时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def set_actor_transform(actor_name: str, location: List[float] = None, rotation: List[float] = None, scale: List[float] = None):
        """
        设置Actor的变换（位置、旋转、缩放）
        
        Args:
            actor_name: Actor名称
            location: [x, y, z] 新位置
            rotation: [pitch, yaw, roll] 新旋转
            scale: [x, y, z] 新缩放
            
        Returns:
            操作结果
        """
        try:
            all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
            
            for actor in all_actors:
                if actor.get_name() == actor_name:
                    # 设置位置（如果提供）
                    if location:
                        location_vector = unreal.Vector(location[0], location[1], location[2])
                        actor.set_actor_location(location_vector, False)
                    
                    # 设置旋转（如果提供）
                    if rotation:
                        rotation_rotator = unreal.Rotator(rotation[0], rotation[1], rotation[2])
                        actor.set_actor_rotation(rotation_rotator, False)
                    
                    # 设置缩放（如果提供）
                    if scale:
                        scale_vector = unreal.Vector(scale[0], scale[1], scale[2])
                        actor.set_actor_scale3d(scale_vector)
                    
                    # 返回更新后的Actor信息
                    actor_info = {
                        "name": actor.get_name(),
                        "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
                        "rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
                        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z]
                    }
                    
                    return {"success": True, "actor": actor_info}
            
            return {"success": False, "message": f"找不到指定的Actor: {actor_name}"}
        except Exception as e:
            logger.error(f"设置Actor变换时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_asset_list(path: str = "/Game/", recursive: bool = True, class_filter: str = None):
        """
        获取内容浏览器中的资产列表
        
        Args:
            path: 内容浏览器路径
            recursive: 是否递归搜索子文件夹
            class_filter: 可选的类过滤器
            
        Returns:
            资产列表
        """
        try:
            # 获取资产注册表
            asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
            
            # 创建过滤器
            ar_filter = unreal.ARFilter(
                package_paths=[path],
                recursive_paths=recursive,
                include_only_on_disk_assets=True
            )
            
            # 如果提供了类过滤器，则添加到过滤器中
            if class_filter:
                ar_filter.class_names = [class_filter]
            
            # 获取资产列表
            assets = asset_registry.get_assets(ar_filter)
            
            # 转换为易于处理的格式
            asset_list = []
            for asset in assets:
                asset_info = {
                    "name": asset.asset_name,
                    "path": asset.object_path,
                    "class": asset.asset_class,
                    "package_name": asset.package_name,
                    "package_path": asset.package_path
                }
                asset_list.append(asset_info)
            
            return asset_list
        except Exception as e:
            logger.error(f"获取资产列表时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def take_screenshot(filename: str = "screenshot.png", width: int = 1920, height: int = 1080, show_ui: bool = False):
        """
        拍摄编辑器视口的截图
        
        Args:
            filename: 截图文件名
            width: 截图宽度
            height: 截图高度
            show_ui: 是否包含UI
            
        Returns:
            截图操作结果
        """
        try:
            # 获取游戏引擎子系统
            gameplay_statics = unreal.GameplayStatics
            
            # 截图保存路径
            screenshot_path = unreal.Paths.project_saved_dir() + "/Screenshots/" + filename
            
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            
            # 拍摄截图
            result = unreal.AutomationLibrary.take_high_res_screenshot(
                width,
                height,
                screenshot_path,
                not show_ui,  # HideUI参数是show_ui的反向值
                False,  # 不使用HDR
                ""  # 空缓冲区名称
            )
            
            return {
                "success": result,
                "path": screenshot_path,
                "width": width,
                "height": height
            }
        except Exception as e:
            logger.error(f"拍摄截图时出错: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def execute_console_command(command: str):
        """
        执行控制台命令
        
        Args:
            command: 要执行的控制台命令
            
        Returns:
            执行结果
        """
        try:
            # 执行控制台命令
            unreal.EditorLevelLibrary.editor_command(command)
            return {"success": True, "command": command}
        except Exception as e:
            logger.error(f"执行控制台命令时出错: {e}")
            return {"error": str(e)}
            
    @staticmethod
    def set_material_parameter(actor_name: str, parameter_name: str, value: Any, component_name: str = None, parameter_type: str = "scalar"):
        """
        设置Actor材质参数
        
        Args:
            actor_name: Actor名称
            parameter_name: 材质参数名称
            value: 要设置的值
            component_name: 可选组件名称
            parameter_type: 参数类型 ("scalar", "vector", "texture")
            
        Returns:
            操作结果
        """
        try:
            # 查找Actor
            all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
            target_actor = None
            
            for actor in all_actors:
                if actor.get_name() == actor_name:
                    target_actor = actor
                    break
            
            if not target_actor:
                return {"success": False, "message": f"找不到指定的Actor: {actor_name}"}
            
            # 查找组件
            mesh_component = None
            if component_name:
                # 如果指定了组件名称，则查找该组件
                components = unreal.EditorFilterLibrary.by_class(
                    target_actor.get_components(),
                    unreal.StaticMeshComponent 
                )
                for component in components:
                    if component.get_name() == component_name:
                        mesh_component = component
                        break
                
                if not mesh_component:
                    return {"success": False, "message": f"找不到指定的组件: {component_name}"}
            else:
                # 如果未指定组件名称，则使用第一个静态网格体组件
                components = unreal.EditorFilterLibrary.by_class(
                    target_actor.get_components(),
                    unreal.StaticMeshComponent 
                )
                
                if len(components) > 0:
                    mesh_component = components[0]
                else:
                    return {"success": False, "message": f"Actor '{actor_name}' 没有静态网格体组件"}
            
            # 获取材质实例
            materials = mesh_component.get_materials()
            if len(materials) == 0:
                return {"success": False, "message": "没有找到可用的材质"}
            
            material = materials[0]
            
            # 确保获取的是材质实例
            if not material.is_a(unreal.MaterialInstanceDynamic):
                material_instance = unreal.MaterialEditingLibrary.create_dynamic_material_instance(
                    target_actor,
                    material, 
                    f"{actor_name}_DynamicMaterial"
                )
            else:
                material_instance = material
            
            # 根据参数类型设置参数值
            if parameter_type.lower() == "scalar":
                material_instance.set_scalar_parameter_value(parameter_name, float(value))
            elif parameter_type.lower() == "vector":
                if isinstance(value, list) and len(value) >= 3:
                    color = unreal.LinearColor(value[0], value[1], value[2], 1.0 if len(value) < 4 else value[3])
                    material_instance.set_vector_parameter_value(parameter_name, color)
                else:
                    return {"success": False, "message": "向量参数必须是包含至少3个元素的列表"}
            elif parameter_type.lower() == "texture":
                # 对于纹理参数，value应该是纹理资产路径
                texture_asset = unreal.load_asset(value)
                if not texture_asset or not texture_asset.is_a(unreal.Texture):
                    return {"success": False, "message": f"找不到纹理资产或资产不是纹理: {value}"}
                material_instance.set_texture_parameter_value(parameter_name, texture_asset)
            else:
                return {"success": False, "message": f"不支持的参数类型: {parameter_type}"}
            
            return {
                "success": True, 
                "actor": actor_name,
                "component": mesh_component.get_name(),
                "parameter": parameter_name,
                "value": value,
                "type": parameter_type
            }
        except Exception as e:
            logger.error(f"设置材质参数时出错: {e}")
            return {"error": str(e)}

# 创建一些直接可调用的辅助函数
def run_python(script_code):
    """直接运行Python代码"""
    return UnrealPythonTools.execute_python(script_code)

def get_actors():
    """获取所有Actor"""
    return UnrealPythonTools.get_all_actors()

def find_actor(name_pattern):
    """按名称查找Actor"""
    return UnrealPythonTools.find_actor_by_name(name_pattern)

def create_actor(class_name, name, location, rotation, scale=None):
    """创建Actor"""
    return UnrealPythonTools.create_actor(class_name, name, location, rotation, scale)

def delete_actor(name):
    """删除Actor"""
    return UnrealPythonTools.delete_actor(name)

def set_transform(actor_name, location=None, rotation=None, scale=None):
    """设置Actor变换"""
    return UnrealPythonTools.set_actor_transform(actor_name, location, rotation, scale)

def get_assets(path="/Game/", recursive=True, class_filter=None):
    """获取资产列表"""
    return UnrealPythonTools.get_asset_list(path, recursive, class_filter)

def take_screenshot(filename="screenshot.png", width=1920, height=1080, show_ui=False):
    """拍摄截图"""
    return UnrealPythonTools.take_screenshot(filename, width, height, show_ui)

def console_command(command):
    """执行控制台命令"""
    return UnrealPythonTools.execute_console_command(command)

def set_material_param(actor, param_name, value, component=None, param_type="scalar"):
    """设置材质参数"""
    return UnrealPythonTools.set_material_parameter(actor, param_name, value, component, param_type) 