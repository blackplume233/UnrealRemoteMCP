// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/UnrealEditorSubsystem.h"
#include "MCPSubsystem.generated.h"

UENUM()
enum EMCPBridgeFuncType
{
	Other,
	Exit,
};

DECLARE_DYNAMIC_DELEGATE_RetVal_TwoParams(bool, FMCPBridgeFuncDelegate,  EMCPBridgeFuncType, Type, const FString&, Message);
DECLARE_DYNAMIC_DELEGATE_OneParam(FMCPBridgeCallback,  const FString&, Message);

USTRUCT(BlueprintType)
struct FMCPContext
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite)
	FMCPBridgeFuncDelegate Bridge;

	UPROPERTY(BlueprintReadWrite)
	bool Running = false;
};
/**
 * 
 */
UCLASS()
class REMOTEMCP_API UMCPSubsystem : public UUnrealEditorSubsystem
{
	GENERATED_BODY()
public:
	UFUNCTION(BlueprintCallable)
	void SetContext(FMCPContext Context);

	UFUNCTION(BlueprintCallable)
	void StartMCP() ;

	UFUNCTION(BlueprintCallable)
	void StopMCP() ;
private:
	FMCPContext MCPContext;
};
