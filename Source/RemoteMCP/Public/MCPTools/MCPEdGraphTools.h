#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MCPEdGraphTools.generated.h"

UCLASS()
class REMOTEMCP_API UMCPEdGraphTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// ──── Existing graph query/edit tools ────

	/** Discover EdGraphs inside any asset. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleFindGraphsInAsset(const FJsonObjectParameter& Params);

	/** List all nodes in an EdGraph. When include_properties=true, returns ExportText for every UPROPERTY. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleListGraphNodes(const FJsonObjectParameter& Params);

	/** Get a single node by guid/name/path (always includes ExportText properties). */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleGetGraphNode(const FJsonObjectParameter& Params);

	/** Delete a node from graph. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleDeleteGraphNode(const FJsonObjectParameter& Params);

	/** Set editor properties on a node (batch set_editor_property). */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleSetNodeProperties(const FJsonObjectParameter& Params);

	/** List all pin connections in the graph. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleListGraphLinks(const FJsonObjectParameter& Params);

	/** Connect two pins. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleConnectPins(const FJsonObjectParameter& Params);

	/** Disconnect all links from a specific pin. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleDisconnectPin(const FJsonObjectParameter& Params);

	/** Add a comment node to the graph. */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleAddCommentNode(const FJsonObjectParameter& Params);

	// ──── New: generic node creation via ImportText ────

	/**
	 * Create any UEdGraphNode subclass by class name, initialize via ImportText, set pin defaults.
	 * @param Params:
	 *   - graph_path (string, required)
	 *   - node_class (string, required) — short name or full path
	 *   - pos_x, pos_y (number, optional)
	 *   - import_text (object, optional) — {PropertyName: "ImportText value"} applied before AllocateDefaultPins
	 *   - pin_defaults (object, optional) — {PinName: "default value text"} applied after AllocateDefaultPins
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleAddNode(const FJsonObjectParameter& Params);

	/**
	 * Set/clear a pin's default value on any node.
	 * @param Params: graph_path, node_guid, pin_name, default_value, default_object (optional), pin_direction (optional)
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleSetPinDefaultValue(const FJsonObjectParameter& Params);

	/**
	 * Compile any Blueprint-derived asset and return diagnostics.
	 * @param Params: asset_path (required)
	 * @return status, has_error, messages[]
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleCompileAsset(const FJsonObjectParameter& Params);

	/**
	 * Create a sub-graph (function/macro) in a Blueprint asset.
	 * @param Params: asset_path, graph_name, graph_type ("function"/"macro", default "function")
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleCreateGraph(const FJsonObjectParameter& Params);

	/**
	 * Delete a sub-graph from an asset.
	 * @param Params: asset_path, graph_name or graph_path
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleDeleteGraph(const FJsonObjectParameter& Params);

	/**
	 * Query asset metadata: parent class, variables, functions, interfaces, components, graphs.
	 * @param Params: asset_path (required)
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|EdGraph")
	static FJsonObjectParameter HandleGetAssetInfo(const FJsonObjectParameter& Params);

private:
	static UEdGraphNode* FindNodeInGraph(UEdGraph* Graph, const FString& NodeGuid, const FString& NodeName, const FString& NodePath);
	static TSharedPtr<FJsonObject> SerializeNode(UEdGraphNode* Node, bool bIncludeProperties = false);
	static TSharedPtr<FJsonObject> SerializePin(UEdGraphPin* Pin);
	static UEdGraphPin* FindPinOnNode(UEdGraphNode* Node, const FString& PinName, const FString& Direction = TEXT(""));
	static bool SaveAssetIfNeeded(const FString& AssetPath);
	static UClass* ResolveNodeClass(const FString& ClassName);
};
