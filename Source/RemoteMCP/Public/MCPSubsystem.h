// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Async/Future.h"
#include "Structure/MCPStructure.h"
#include "Subsystems/UnrealEditorSubsystem.h"
#include "MCPSubsystem.generated.h"



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
	void PostEngineInit();
	void PostPythonInit();
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintCallable)
	void StartMCP() ;
	UFUNCTION(BlueprintCallable)
	void StopMCP() ;

	UFUNCTION(BlueprintCallable)
	EMCPServerState GetMCPServeState() const;
private:
	UFUNCTION(BlueprintCallable)
	void SetupObject(FMCPObject Context);
	UFUNCTION(BlueprintCallable)
	void ClearObject();
private:
	UPROPERTY()
	FMCPObject MCPContext;
	TFuture<void> RunTread;
	int TickCount = 0;
	static constexpr int TickInterval = 10;
	bool WaitStart = false;
};
