#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MCPBehaviorTreeTools.generated.h"

UCLASS()
class REMOTEMCP_API UMCPBehaviorTreeTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// AI(GPT-5.2): 说明
	// - Python 侧无法读取 BehaviorTreeGraph 的 Nodes（UE Python wrapper 将其标记为 protected）。
	// - 因此提供 C++ Bridge：列节点 / 加节点 / 连线，保证可以自动化“创建可用行为树”流程。

	/**
	 * 获取行为树的Graph路径
	 * @param Params - 必须包含"bt_path"
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|BehaviorTree")
	static FJsonObjectParameter HandleGetBehaviorTreeGraph(const FJsonObjectParameter& Params);

	/**
	 * 创建行为树资产
	 * @param Params - 必须包含"name", 可选"package_path"
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|BehaviorTree")
	static FJsonObjectParameter HandleCreateBehaviorTree(const FJsonObjectParameter& Params);
    
    /**
	 * 获取行为树节点的所有辅助节点 (Decorators, Services)
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|BehaviorTree")
	static FJsonObjectParameter HandleGetBTAuxiliaryNodes(const FJsonObjectParameter& Params);

	/**
	 * 列出 BehaviorTreeGraph 内所有节点（包含 pins 基础信息）。
	 * @param Params - 必须包含 "graph_path"
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|BehaviorTree")
	static FJsonObjectParameter HandleListBTGraphNodes(const FJsonObjectParameter& Params);

	/**
	 * 在 BehaviorTreeGraph 内新增一个节点（Task/Composite）。
	 * @param Params - 必须包含:
	 *   - graph_path: 目标图路径
	 *   - bt_node_class: 运行时 BT 节点类（如 "/Script/AIModule.BTTask_Wait" 或 "BTTask_Wait"）
	 *   - pos_x/pos_y: 可选
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|BehaviorTree")
	static FJsonObjectParameter HandleAddBTGraphNode(const FJsonObjectParameter& Params);

	/**
	 * 连接行为树节点（父->子）。默认连接 parent 的第0个输出 pin 到 child 的第0个输入 pin。
	 * @param Params - 必须包含:
	 *   - graph_path
	 *   - parent_node_path
	 *   - child_node_path
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|BehaviorTree")
	static FJsonObjectParameter HandleConnectBTGraphNodes(const FJsonObjectParameter& Params);
};
