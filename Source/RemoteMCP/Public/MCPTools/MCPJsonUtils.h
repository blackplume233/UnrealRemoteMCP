// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "UObject/Object.h"
#include "MCPJsonUtils.generated.h"

/**
 * 
 */
UCLASS()
class REMOTEMCP_API UMCPJsonUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
public:
	UFUNCTION(Blueprintable, BlueprintPure, Category = "MCP|Json")
	static FJsonObjectParameter MakeJsonObject(const FString& JsonString);

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "MCP|Json")
	static FString JsonObjectToString(const FJsonObjectParameter& JsonObject);
};
