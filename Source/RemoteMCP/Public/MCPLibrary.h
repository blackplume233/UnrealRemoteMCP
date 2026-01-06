// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MCPLibrary.generated.h"

/**
 * 
 */
UCLASS(Blueprintable)
class REMOTEMCP_API UMCPLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|RemoteMCP")
	static void StartMCP();

	UFUNCTION(BlueprintCallable ,Category="MCPLibrary|RemoteMCP")
	static void StopMCP();
};
