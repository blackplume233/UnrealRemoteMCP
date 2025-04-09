// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPLibrary.h"

#include "IPythonScriptPlugin.h"
#include "IPythonScriptPlugin.h"
#include "K2Node_GetSubsystem.h"
#include "MCPSubsystem.h"

void UMCPLibrary::StartMCP()
{
	GEditor->GetEditorSubsystem<UMCPSubsystem>()->StartMCP();
}

void UMCPLibrary::StopMCP()
{
	GEditor->GetEditorSubsystem<UMCPSubsystem>()->StopMCP();
}
