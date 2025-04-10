// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPPythonBridge.h"
#include "MCPMisc.h"

template<class CharType, class PrintPolicy>
bool UStructToJsonObjectStringInternal(const TSharedRef<FJsonObject>& JsonObject, FString& OutJsonString, int32 Indent)
{
	TSharedRef<TJsonWriter<CharType, PrintPolicy> > JsonWriter = TJsonWriterFactory<CharType, PrintPolicy>::Create(&OutJsonString, Indent);
	bool bSuccess = FJsonSerializer::Serialize(JsonObject, JsonWriter);
	JsonWriter->Close();
	return bSuccess;
}

FString UMCPPythonBridge::ConvertJsonObjectToString(const TSharedRef<FJsonObject>& JsonObject)
{
	FString Ret;
	UStructToJsonObjectStringInternal<TCHAR,TPrettyJsonPrintPolicy<TCHAR>>(JsonObject, Ret, 0);
	return Ret;
}

FString UMCPPythonBridge::SearchConsoleCommands(FString KeyWords)
{
	TSharedPtr<FJsonObject> Ret = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> JsonArray{};
	auto Visitor = [&JsonArray](const TCHAR* Name, IConsoleObject* Object)
	{
		TSharedPtr<FJsonObject> JsonObject = MakeShared<FJsonObject>();
		JsonObject->SetStringField(TEXT("Key"), Name);
		JsonObject->SetStringField(TEXT("Help"), Object->GetHelp());
		TSharedPtr<FJsonValue> JsonValuePtr = MakeShared<FJsonValueObject>(JsonObject);
		JsonArray.Add(JsonValuePtr);
	};
	IConsoleManager::Get().ForEachConsoleObjectThatContains(FConsoleObjectVisitor::CreateLambda(Visitor),GetData(KeyWords));
	Ret->SetArrayField(TEXT("ConsoleObjects"), JsonArray);
	return ConvertJsonObjectToString(Ret.ToSharedRef());
}

