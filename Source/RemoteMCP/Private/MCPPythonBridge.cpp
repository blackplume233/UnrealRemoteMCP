// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPPythonBridge.h"
#include "MCPMisc.h"
#include "MCPUtility.h"
#include "Interfaces/IPluginManager.h"




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
	return UMCPUtility::ConvertJsonObjectToString(Ret.ToSharedRef());
}

FString UMCPPythonBridge::PluginDirectory(FString PluginName)
{
	return IPluginManager::Get().FindPlugin(PluginName)->GetBaseDir();
}


FString UMCPPythonBridge::SafeCallCPPFunction(FMCPCommandDelegate Callable, const FString& Parameter)
{

	if (!Callable.IsBound())
	{
		return "{}";
	}
	FJsonObjectParameter JsonObjectParameter{};
	JsonObjectParameter.JsonObjectFromString(Parameter);

	try
	{
		FJsonObjectParameter Result = Callable.Execute(JsonObjectParameter);
		return Result.ConvertToString();
	}
	catch (std::exception e)
	{
		auto JsonObject = MakeShared<FJsonObject>();
		auto Error = FString::Printf(TEXT("Error: %s"), *FString(e.what()));
		JsonObject->SetStringField(TEXT("error"), Error);
		return UMCPUtility::ConvertJsonObjectToString(JsonObject);
	}
}

