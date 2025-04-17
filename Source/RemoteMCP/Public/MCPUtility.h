// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"


#include "MCPUtility.generated.h"

/**
 * 
 */
UCLASS()
class REMOTEMCP_API UMCPUtility : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
public:
	static TSharedRef<FJsonObject> ConvertStringToJsonObject(const FString& JsonString);
	static FString ConvertJsonObjectToString(const TSharedRef<FJsonObject>& JsonObject);
};
