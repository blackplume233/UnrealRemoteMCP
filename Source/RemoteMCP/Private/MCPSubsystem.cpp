// Fill out your copyright notice in the Description page of Project Settings.

#include "MCPSubsystem.h"
#include "Async/Future.h"
#include "IPythonScriptPlugin.h"
#include "MCPSetting.h"

void UMCPSubsystem::Tick(float DeltaTime)
{
	if (!MCPContext.IsRunning())
	{
		if (!MCPContext.GUID.IsEmpty() && !MCPContext.Bridge.IsBound())
		{
			SetupBridge();// 如果应该存在，则尝试重新构建
		}
		return;
	}

	TickCount++;
	if (TickCount % TickInterval == 0)
	{
		TickCount = TickCount % 86400;
		try
		{
			bool Ret = MCPContext.Tick.IsBound() && MCPContext.Tick.Execute();
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
#if ENGINE_MINOR_VERSION >= 7
	if (IPythonScriptPlugin::Get()->IsPythonInitialized())
	{
		PostPythonInit();
	}
	else
	{
		IPythonScriptPlugin::Get()->OnPythonInitialized().AddUObject(this, &UMCPSubsystem::PostEngineInit);
	}
#else
	FEditorDelegates::OnEditorInitialized.AddLambda([](double duration)
	{
		if (auto* SubSystem = UMCPSubsystem::Get())
		{
			SubSystem->PostPythonInit();
		}
	});
#endif
}

void UMCPSubsystem::PostPythonInit()
{
	if (GetDefault<UMCPSetting>()->bAutoStart)
	{
		StartMCP();
	}
}

void UMCPSubsystem::SetupBridge()
{
	FPythonCommandEx CommandEx;
	CommandEx.Command = TEXT("init_mcp.py");
	CommandEx.FileExecutionScope = EPythonFileExecutionScope::Private;
	IPythonScriptPlugin::Get()->ExecPythonCommandEx(CommandEx);
}

bool UMCPSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	return Super::ShouldCreateSubsystem(Outer) && GetDefault<UMCPSetting>()->bEnable;
}

void UMCPSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	// AI(GPT-5.2): 修复编译错误：移除误入的调试字符串 "aaa"
	UMCPSubsystem::PostEngineInit();
	// FCoreUObjectDelegates::ReloadCompleteDelegate.AddLambda([this](EReloadCompleteReason Reason)
	// {
	// 	if (auto* SubSystem = UMCPSubsystem::Get())
	// 	{
	// 		SubSystem->StopMCP();
	// 		ClearObject();
	// 	}
	// });
}

void UMCPSubsystem::PostCDOCompiled(const FPostCDOCompiledContext& Context)
{
	Super::PostCDOCompiled(Context);
}

UMCPSubsystem* UMCPSubsystem::Get()
{
	return GEditor->GetEditorSubsystem<UMCPSubsystem>();
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
	// StopMCP();
	if (MCPContext.IsRunning())
	{
		UE_LOG(LogTemp, Error, TEXT("MCP Already Running"));
		return;
	}

	// auto Command = TEXT("init_mcp.py");
	SetupBridge();
	if (MCPContext.Valid())
	{
		RunTread = Async(EAsyncExecution::Thread, [this]()
		{
			// Your code to start the MCP goes here
			try
			{
				MCPContext.Bridge.Execute(EMCPBridgeFuncType::Start, TEXT("MCP Start"));
			}
			catch (...)
			{
			}
		});
	}

	// auto Command = TEXT("init_mcp.py");
	// IPythonScriptPlugin::Get()->ExecPythonCommand(Command);
}

void UMCPSubsystem::Reload()
{
	if (MCPContext.IsRunning())
	{
		bool Ret = MCPContext.Bridge.Execute(EMCPBridgeFuncType::Reload, TEXT("Reload"));
	}
}

void UMCPSubsystem::StopMCP()
{
	if (!MCPContext.IsRunning())
		return;
	if (MCPContext.Bridge.IsBound())
	{
		auto _ = MCPContext.Bridge.Execute(EMCPBridgeFuncType::Exit, TEXT("MCP Stopped"));
		RunTread.WaitFor(FTimespan::FromSeconds(100));
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
