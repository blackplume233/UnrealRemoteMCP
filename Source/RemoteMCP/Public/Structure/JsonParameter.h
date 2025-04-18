// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "JsonObjectWrapper.h"
#include "GameFramework/Actor.h"
#include "JsonParameter.generated.h"

USTRUCT(BlueprintType, meta = (DisplayName = "JsonObject"))
struct FJsonObjectParameter
{
	GENERATED_BODY()

public:
	FJsonObjectParameter(const FJsonObjectWrapper& Other)
	{
		JsonString = Other.JsonString;
		JsonObject = Other.JsonObject;
	}

	FJsonObjectParameter(const TSharedPtr<FJsonObject>& Other)
	{
		JsonObject = Other;
		if (JsonObject.IsValid())
		{
			JsonObjectToString(JsonString);
		}
	}

	FJsonObjectParameter(const TSharedRef<FJsonObject>& Other) : FJsonObjectParameter(Other.ToSharedPtr())
	{

	}
private:
	UPROPERTY(EditAnywhere, Category = "JSON")
	FString JsonString;
public:
	REMOTEMCP_API FJsonObjectParameter();






	REMOTEMCP_API bool ImportTextItem(const TCHAR*& Buffer, int32 PortFlags, UObject* Parent, FOutputDevice* ErrorText);
	REMOTEMCP_API bool ExportTextItem(FString& ValueStr, FJsonObjectParameter const& DefaultValue, UObject* Parent, int32 PortFlags, UObject* ExportRootScope) const;
	REMOTEMCP_API void PostSerialize(const FArchive& Ar);

	REMOTEMCP_API explicit operator bool() const;

	REMOTEMCP_API bool JsonObjectToString(FString& Str) const;
	REMOTEMCP_API bool JsonObjectFromString(const FString& Str);

	/**
	 * Returns the memory allocated by this object in Bytes, should NOT include sizeof(*this).
	 */
	REMOTEMCP_API SIZE_T GetAllocatedSize() const;


	[[nodiscard]] FORCEINLINE FJsonObject* operator->() const
	{
		if (JsonObject.IsValid())
		{
			return JsonObject.Get();
		}
		return &EmptyDefaultObject;
	}

	operator TSharedPtr<FJsonObject>()
	{
		return JsonObject;
	}

	operator const TSharedPtr<FJsonObject>&() const
	{
		return JsonObject;
	}

	const TSharedPtr<FJsonObject>& GetJsonObject() const
	{
		return JsonObject;
	}
private:
	TSharedPtr<FJsonObject> JsonObject;
	static FJsonObject EmptyDefaultObject;
};
