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
class REMOTEMCP_API UMCPSubsystem : public UEditorSubsystem, public FTickableGameObject
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
	virtual void Deinitialize() override;

#pragma endregion
	void PostEngineInit();
	void PostPythonInit();
	void SetupBridge();
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void PostCDOCompiled(const FPostCDOCompiledContext& Context) override;
	
	UFUNCTION(BlueprintCallable ,Category="MCPLibrary|RemoteMCP")
	static UMCPSubsystem* Get();
	UFUNCTION(BlueprintCallable ,Category="MCPLibrary|RemoteMCP")
	void StartMCP() ;
	UFUNCTION(BlueprintCallable ,Category="MCPLibrary|RemoteMCP")
	void Reload();
	UFUNCTION(BlueprintCallable ,Category="MCPLibrary|RemoteMCP")
	void StopMCP() ;

	UFUNCTION(BlueprintCallable ,Category="MCPLibrary|RemoteMCP")
	EMCPServerState GetMCPServeState() const;
private:
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|RemoteMCP")
	void SetupObject(FMCPObject Context);
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|RemoteMCP")
	void ClearObject();
private:
	// Keep delegate wrappers reachable by GC; a static non-UPROPERTY FMCPObject can
	// leave Python delegate wrappers dangling and crash inside delegate dispatch.
	UPROPERTY(Transient)
	FMCPObject MCPContext;
	TFuture<void> RunTread;
	int TickCount = 0;
	static constexpr int TickInterval = 2;
	bool WaitStart = false;
};
