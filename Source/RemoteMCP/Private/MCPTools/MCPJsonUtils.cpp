// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPTools/MCPJsonUtils.h"

FJsonObjectParameter UMCPJsonUtils::MakeJsonObject(const FString& JsonString)
{
	FJsonObjectParameter JsonObject;
	JsonObject.JsonObjectFromString(JsonString);
	return JsonObject;
}

FString UMCPJsonUtils::JsonObjectToString(const FJsonObjectParameter& JsonObject)
{
	FString JsonString;
	JsonObject.JsonObjectToString(JsonString);
	return JsonString;
}
