// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPSubsystem.h"

#include "IPythonScriptPlugin.h"

void UMCPSubsystem::SetContext(FMCPContext Context)
{
	this->MCPContext = Context;
}

void UMCPSubsystem::StartMCP()
{
	StopMCP();
	AsyncTask(ENamedThreads::AnyNormalThreadNormalTask, []()
	{
		// Your code to start the MCP goes here
		auto Command = TEXT("init_mcp.py");
		IPythonScriptPlugin::Get()->ExecPythonCommand(Command);
	});
}

void UMCPSubsystem::StopMCP()
{
	if (!MCPContext.Running || !MCPContext.Bridge.IsBound()) return;
	auto _= MCPContext.Bridge.Execute(EMCPBridgeFuncType::Exit, TEXT("MCP Stopped"));
}
