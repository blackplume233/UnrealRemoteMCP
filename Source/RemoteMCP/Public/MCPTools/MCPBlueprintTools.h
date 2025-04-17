#pragma once

#include "CoreMinimal.h"
#include "JsonObjectWrapper.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Structure/JsonParameter.h"
#include "MCPBlueprintTools.generated.h"

/**
 * Reference https://github.com/chongdashu/unreal-mcp
 */
UCLASS()
class REMOTEMCP_API UMCPBlueprintTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

	/**
	 * 创建一个新的蓝图。
	 * @param Params 包含蓝图创建所需的参数。
	 * - name (string): 蓝图名称。
	 * - package_path (string, optional): 蓝图的包路径，默认为 "/Game/Blueprints/"。
	 * - parent_class (string, optional): 父类名称，默认为 "AActor"。
	 * @return 包含蓝图创建结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleCreateBlueprint(const FJsonObjectParameter& Params);

	/**
	 * 向蓝图添加组件。
	 * @param Params 包含组件添加所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - component_type (string): 组件类型。
	 * - component_name (string): 组件名称。
	 * - location (array<float>, optional): 组件的位置 [x, y, z]。
	 * - rotation (array<float>, optional): 组件的旋转 [pitch, yaw, roll]。
	 * - scale (array<float>, optional): 组件的缩放 [x, y, z]。
	 * @return 包含组件添加结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddComponentToBlueprint(const FJsonObjectParameter& Params);

	/**
	 * 设置蓝图中组件的属性。
	 * @param Params 包含属性设置所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - component_name (string): 组件名称。
	 * - property_name (string): 属性名称。
	 * - property_value (any): 属性值，支持多种类型（如数字、布尔值、字符串等）。
	 * @return 包含属性设置结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetComponentProperty(const FJsonObjectParameter& Params);

	/**
	 * 设置组件的物理属性。
	 * @param Params 包含物理属性设置所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - component_name (string): 组件名称。
	 * - simulate_physics (bool, optional): 是否启用物理模拟。
	 * - mass (float, optional): 组件质量。
	 * - linear_damping (float, optional): 线性阻尼。
	 * - angular_damping (float, optional): 角阻尼。
	 * @return 包含物理属性设置结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetPhysicsProperties(const FJsonObjectParameter& Params);

	/**
	 * 编译蓝图。
	 * @param Params 包含蓝图编译所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * @return 包含编译结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleCompileBlueprint(const FJsonObjectParameter& Params);

	/**
	 * 在场景中生成蓝图实例。
	 * @param Params 包含生成蓝图实例所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - actor_name (string): 实例化的Actor名称。
	 * - location (array<float>, optional): 实例的位置 [x, y, z]。
	 * - rotation (array<float>, optional): 实例的旋转 [pitch, yaw, roll]。
	 * @return 包含生成结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSpawnBlueprintActor(const FJsonObjectParameter& Params);

	/**
	 * 设置蓝图默认对象的属性。
	 * @param Params 包含属性设置所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - property_name (string): 属性名称。
	 * - property_value (any): 属性值，支持多种类型（如数字、布尔值、字符串等）。
	 * @return 包含属性设置结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetBlueprintProperty(const FJsonObjectParameter& Params);

	/**
	 * 设置静态网格组件的属性。
	 * @param Params 包含静态网格属性设置所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - component_name (string): 组件名称。
	 * - static_mesh (string, optional): 静态网格路径。
	 * - material (string, optional): 材质路径。
	 * @return 包含设置结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetStaticMeshProperties(const FJsonObjectParameter& Params);

	/**
	 * 设置Pawn的属性。
	 * @param Params 包含Pawn属性设置所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - auto_possess_player (string, optional): 自动控制玩家。
	 * - use_controller_rotation_yaw (bool, optional): 是否使用控制器旋转Yaw。
	 * - use_controller_rotation_pitch (bool, optional): 是否使用控制器旋转Pitch。
	 * - use_controller_rotation_roll (bool, optional): 是否使用控制器旋转Roll。
	 * - can_be_damaged (bool, optional): 是否可以被伤害。
	 * @return 包含设置结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetPawnProperties(const FJsonObjectParameter& Params);

#pragma region operate node
	
	/**
	 * 连接蓝图中的两个节点。
	 * @param Params 包含节点连接所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - source_node_id (string): 源节点的ID。
	 * - target_node_id (string): 目标节点的ID。
	 * - source_pin (string): 源节点引脚名称。
	 * - target_pin (string): 目标节点引脚名称。
	 * @return 包含连接结果的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleConnectBlueprintNodes(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中添加获取组件引用的节点。
	 * @param Params 包含节点创建所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - component_name (string): 要引用的组件名称。
	 * - node_position (array<float>, optional): 节点在图表中的位置 [x, y]。
	 * @return 包含新节点信息的 JSON 对象，包括节点ID。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddBlueprintGetSelfComponentReference(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中添加事件节点。
	 * @param Params 包含事件节点创建所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - event_name (string): 事件名称（如BeginPlay, Tick等）。
	 * - node_position (array<float>, optional): 节点在图表中的位置 [x, y]。
	 * @return 包含新节点信息的 JSON 对象，包括节点ID。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddBlueprintEvent(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中添加函数调用节点。
	 * @param Params 包含函数调用节点创建所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - function_name (string): 要调用的函数名称。
	 * - target (string, optional): 目标类名称，如果不提供则默认为蓝图自身。
	 * - params (object, optional): 函数参数的名称和值的映射。
	 * - node_position (array<float>, optional): 节点在图表中的位置 [x, y]。
	 * @return 包含新节点信息的 JSON 对象，包括节点ID。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddBlueprintFunctionCall(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中添加变量。
	 * @param Params 包含变量创建所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - variable_name (string): 变量名称。
	 * - variable_type (string): 变量类型（如Boolean, Integer, Float, String, Vector等）。
	 * - is_exposed (bool, optional): 是否在编辑器中暴露变量，默认为false。
	 * @return 包含新变量信息的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddBlueprintVariable(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中添加输入动作节点。
	 * @param Params 包含输入动作节点创建所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - action_name (string): 输入动作名称。
	 * - node_position (array<float>, optional): 节点在图表中的位置 [x, y]。
	 * @return 包含新节点信息的 JSON 对象，包括节点ID。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddBlueprintInputActionNode(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中添加自引用节点（Self节点）。
	 * @param Params 包含自引用节点创建所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - node_position (array<float>, optional): 节点在图表中的位置 [x, y]。
	 * @return 包含新节点信息的 JSON 对象，包括节点ID。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleAddBlueprintSelfReference(const FJsonObjectParameter& Params);

	/**
	 * 在蓝图中查找特定类型的节点。
	 * @param Params 包含节点查找所需的参数。
	 * - blueprint_name (string): 蓝图名称。
	 * - node_type (string): 节点类型（如Event, InputAction等）。
	 * - event_name (string, optional): 当查找Event类型节点时的事件名称。
	 * @return 包含找到的节点ID列表的 JSON 对象。
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleFindBlueprintNodes(const FJsonObjectParameter& Params);
#pragma endregion
};
