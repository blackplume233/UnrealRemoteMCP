// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "MCPSetting.generated.h"

/**
 * 
 */
UCLASS(Config=EditorPerProjectUserSettings)
class REMOTEMCP_API UMCPSetting : public UDeveloperSettings
{
	GENERATED_BODY()
	UMCPSetting();
public:
	UPROPERTY(Config, BlueprintReadWrite, EditAnywhere, Category = "MCP")
	int Port = 8422;
	UPROPERTY(Config, BlueprintReadWrite, EditAnywhere, Category = "MCP")
	bool bAutoStart = true;
};
