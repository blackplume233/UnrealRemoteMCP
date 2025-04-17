// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MCPPythonBridge.generated.h"

/**
 * 
 */
UCLASS()
class REMOTEMCP_API UMCPPythonBridge : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
private:
	UFUNCTION(BlueprintCallable, Category="MCP")
	static FString SearchConsoleCommands(FString KeyWords);
	UFUNCTION(BlueprintCallable, Category="MCP")
	static FString PluginDirectory(FString PluginName);

#pragma region Blueprint

#pragma endregion
};
