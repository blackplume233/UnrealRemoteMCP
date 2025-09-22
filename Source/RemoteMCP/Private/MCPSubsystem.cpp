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

void UMCPSubsystem::PostEngineInit()
{
	if (IPythonScriptPlugin::Get()->IsPythonInitialized()) {
		PostPythonInit();
	}
	else {
		IPythonScriptPlugin::Get()->OnPythonInitialized().AddUObject(this, &UMCPSubsystem::PostEngineInit);
	}
	
}

void UMCPSubsystem::PostPythonInit()
{
	if (GetDefault<UMCPSetting>()->bAutoStart)
	{
		StartMCP();
	}
}

void UMCPSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	
	FCoreDelegates::OnFEngineLoopInitComplete.AddUObject(this, &UMCPSubsystem::PostEngineInit);
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

	//auto Command = TEXT("init_mcp.py");
	FPythonCommandEx CommandEx ;
	CommandEx.Command = TEXT("init_mcp.py");
	CommandEx.FileExecutionScope = EPythonFileExecutionScope::Private;
	IPythonScriptPlugin::Get()->ExecPythonCommandEx(CommandEx);
	if (MCPContext.Valid())
	{
		RunTread = Async(EAsyncExecution::Thread, [this]()
			{
				// Your code to start the MCP goes here
				MCPContext.Bridge.Execute(EMCPBridgeFuncType::Start, TEXT("MCP Start"));
			});
	}

	// auto Command = TEXT("init_mcp.py");
	// IPythonScriptPlugin::Get()->ExecPythonCommand(Command);

}

void UMCPSubsystem::StopMCP()
{
	if (!MCPContext.Valid() ) return;
	if (MCPContext.Bridge.IsBound()) {
		auto _ = MCPContext.Bridge.Execute(EMCPBridgeFuncType::Exit, TEXT("MCP Stopped"));
		RunTread.WaitFor(FTimespan::FromSeconds(10));
	}

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
