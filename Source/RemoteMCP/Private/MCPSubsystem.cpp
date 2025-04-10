// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPSubsystem.h"
#include "Async/Future.h"
#include "IPythonScriptPlugin.h"
#include "MCPSetting.h"

void UMCPSubsystem::Tick(float DeltaTime)
{
	if (!MCPContext.Valid() && !MCPContext.Bridge.IsBound())
	{
		return;
	}

	TickCount ++;
	if (TickCount % TickInterval == 0)
	{
		TickCount = TickCount % 86400;
		try
		{
			bool Ret = MCPContext.Tick.ExecuteIfBound();
			if (!Ret)
			{
				UE_LOG(LogTemp, Error, TEXT("MCP Tick Failed"));
				StopMCP();
			}
		}
		catch (...)
		{
			UE_LOG(LogTemp, Error, TEXT("MCP Tick Error"));
			StopMCP();
		}

	}
}

void UMCPSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (GetDefault<UMCPSetting>()->bAutoStart)
	{
		StartMCP();
	}
}

void UMCPSubsystem::SetupObject(FMCPObject Context)
{
	this->MCPContext = Context;
	WaitStart = true;
}

void UMCPSubsystem::ClearObject()
{
	this->MCPContext = FMCPObject();
}

void UMCPSubsystem::StartMCP()
{
	//StopMCP();
	if (MCPContext.Valid())
	{
		UE_LOG(LogTemp, Error, TEXT("MCP Already Running"));
		return;
	}
	RunTread = Async(EAsyncExecution::Thread, []()
	{
		// Your code to start the MCP goes here
		auto Command = TEXT("init_mcp.py");
		IPythonScriptPlugin::Get()->ExecPythonCommand(Command);
	});
	// auto Command = TEXT("init_mcp.py");
	// IPythonScriptPlugin::Get()->ExecPythonCommand(Command);

}

void UMCPSubsystem::StopMCP()
{
	if (!MCPContext.Valid()) return;
	auto _= MCPContext.Bridge.Execute(EMCPBridgeFuncType::Exit, TEXT("MCP Stopped"));
	RunTread.Wait();
	//ClearObject();
}

EMCPServerState UMCPSubsystem::GetMCPServeState() const
{
	if (MCPContext.Valid())
	{
		return EMCPServerState::Runing;
	}
	return EMCPServerState::Stop;
}
