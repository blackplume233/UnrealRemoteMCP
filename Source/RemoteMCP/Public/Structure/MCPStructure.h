// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "JsonParameter.h"
#include "UObject/Object.h"
#include "MCPStructure.generated.h"

UENUM()
enum EMCPBridgeFuncType
{
	Other,
	Exit,
	Start,
	//HeartbeatPacket,
};



UENUM(BlueprintType)
enum EMCPServerState
{
	None,
	Runing,
	Stop,
};


DECLARE_DYNAMIC_DELEGATE_RetVal_TwoParams(bool, FMCPBridgeFuncDelegate,  EMCPBridgeFuncType, Type, const FString&, Message);
DECLARE_DYNAMIC_DELEGATE_OneParam(FMCPBridgeCallback,  const FString&, Message);
DECLARE_DYNAMIC_DELEGATE(FMCPObjectEventFunction);
DECLARE_DYNAMIC_DELEGATE_RetVal_OneParam(FJsonObjectParameter,FMCPCommandDelegate, FJsonObjectParameter, Parameter);

USTRUCT(BlueprintType)
struct FMCPObject
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadWrite,Category="MCPLibrary|RemoteMCP")
	FMCPBridgeFuncDelegate Bridge;

	UPROPERTY(BlueprintReadWrite,Category="MCPLibrary|RemoteMCP")
	FMCPObjectEventFunction Tick;

	UPROPERTY(BlueprintReadWrite,Category="MCPLibrary|RemoteMCP")
	FString GUID;

	UPROPERTY(BlueprintReadWrite,Category="MCPLibrary|RemoteMCP")
	TObjectPtr<UObject> PythonObjectHandle;

	bool Valid() const
	{
		return PythonObjectHandle.Get() != nullptr;
	}
};
