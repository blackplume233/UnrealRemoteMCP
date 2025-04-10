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
public:
	static FString ConvertJsonObjectToString(const TSharedRef<FJsonObject>& JsonObject);

private:
	UFUNCTION(BlueprintCallable)
	static FString SearchConsoleCommands(FString KeyWords);

};
