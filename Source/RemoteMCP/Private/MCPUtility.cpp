// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPUtility.h"

#include "JsonObjectConverter.h"

template<class CharType, class PrintPolicy>
bool UStructToJsonObjectStringInternal(const TSharedRef<FJsonObject>& JsonObject, FString& OutJsonString, int32 Indent)
{
	TSharedRef<TJsonWriter<CharType, PrintPolicy> > JsonWriter = TJsonWriterFactory<CharType, PrintPolicy>::Create(&OutJsonString, Indent);
	bool bSuccess = FJsonSerializer::Serialize(JsonObject, JsonWriter);
	JsonWriter->Close();
	return bSuccess;
}


TSharedRef<FJsonObject> UMCPUtility::ConvertStringToJsonObject(const FString& JsonString)
{
	TSharedPtr<FJsonObject> JsonObject = MakeShared<FJsonObject>();
	TSharedRef<TJsonReader<>> JsonReader = TJsonReaderFactory<>::Create(JsonString);
	FJsonSerializer::Deserialize(JsonReader, JsonObject);
	return JsonObject.ToSharedRef();
}

FString UMCPUtility::ConvertJsonObjectToString(const TSharedRef<FJsonObject>& JsonObject)
{
	FString Ret;
	UStructToJsonObjectStringInternal<TCHAR,TPrettyJsonPrintPolicy<TCHAR>>(JsonObject, Ret, 0);
	return Ret;
}