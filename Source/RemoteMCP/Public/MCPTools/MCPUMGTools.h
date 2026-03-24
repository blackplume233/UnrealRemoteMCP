// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "UObject/Object.h"
#include "MCPUMGTools.generated.h"

/**
 * rReference https://github.com/chongdashu/unreal-mcp
 */
UCLASS()
class REMOTEMCP_API UMCPUMGTools : public UObject
{
	GENERATED_BODY()
public:
	    /**
     * Create a new UMG Widget Blueprint
     * @param Params - Must include "name" for the blueprint name
     * @return JSON response with the created blueprint details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static
    FJsonObjectParameter HandleCreateUMGWidgetBlueprint(const FJsonObjectParameter& Params);

	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static
    FJsonObjectParameter HandleAddWidgetToViewport(const FJsonObjectParameter& Params);

	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static
    FJsonObjectParameter HandleBindWidgetEvent(const FJsonObjectParameter& Params);

	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
    static FJsonObjectParameter HandleClearWidgetTree(const FJsonObjectParameter& Params);

	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
    static FJsonObjectParameter HandleAddWidget(const FJsonObjectParameter& Params);

	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
    static FJsonObjectParameter HandleRemoveWidget(const FJsonObjectParameter& Params);

	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
    static FJsonObjectParameter HandleGetWidgetTree(const FJsonObjectParameter& Params);
};
