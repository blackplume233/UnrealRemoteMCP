// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPLibrary.h"

#include "IPythonScriptPlugin.h"
#include "IPythonScriptPlugin.h"
#include "K2Node_GetSubsystem.h"
#include "MCPSubsystem.h"

void UMCPLibrary::StartMCP()
{
	UMCPSubsystem::Get()->StartMCP();
}

void UMCPLibrary::StopMCP()
{
	UMCPSubsystem::Get()->StopMCP();
}
