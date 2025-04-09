// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Async/Future.h"
#include "Subsystems/UnrealEditorSubsystem.h"
#include "MCPSubsystem.generated.h"

UENUM()
enum EMCPBridgeFuncType
{
	Other,
	Exit,
	Start,
	//HeartbeatPacket,
};

DECLARE_DYNAMIC_DELEGATE_RetVal_TwoParams(bool, FMCPBridgeFuncDelegate,  EMCPBridgeFuncType, Type, const FString&, Message);
DECLARE_DYNAMIC_DELEGATE_OneParam(FMCPBridgeCallback,  const FString&, Message);
DECLARE_DYNAMIC_DELEGATE(FMCPObjectEventFunction);

UENUM(BlueprintType)
enum EMCPObjectState
{
	None,
	Living,
};

USTRUCT(BlueprintType)
struct FMCPObject
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadWrite)
	FMCPBridgeFuncDelegate Bridge;

	UPROPERTY(BlueprintReadWrite)
	FMCPObjectEventFunction Tick;

	UPROPERTY(BlueprintReadWrite)
	FString GUID;

	UPROPERTY(BlueprintReadWrite)
	TObjectPtr<UObject> PythonObjectHandle;

	bool Valid() const
	{
		return Bridge.IsBound() ;
	}
};
/**
 * 
 */
UCLASS()
class REMOTEMCP_API UMCPSubsystem : public UUnrealEditorSubsystem, public FTickableGameObject
{
	GENERATED_BODY()
public:

#pragma region FTickableGameObject
	virtual TStatId GetStatId() const override
	{
		RETURN_QUICK_DECLARE_CYCLE_STAT(UMCPSubsystem, STATGROUP_Tickables);
	}

	virtual bool IsTickable() const override
	{
		return true;
	}

	virtual bool IsTickableInEditor() const override
	{
		return true;
	};

	virtual ETickableTickType GetTickableTickType() const override
	{
		return ETickableTickType::Always;
	}

	virtual void Tick(float DeltaTime) override;
#pragma endregion


	UFUNCTION(BlueprintCallable)
	void SetupObject(FMCPObject Context);

	UFUNCTION(BlueprintCallable)
	void ClearObject();

	UFUNCTION(BlueprintCallable)
	void StartMCP() ;

	UFUNCTION(BlueprintCallable)
	void StopMCP() ;
private:
	UPROPERTY()
	FMCPObject MCPContext;
	TFuture<void> RunTread;
	int TickCount = 0;
	static constexpr int TickInterval = 10;
	bool WaitStart = false;
};
