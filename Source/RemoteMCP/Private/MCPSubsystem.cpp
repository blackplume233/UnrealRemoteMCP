// Fill out your copyright notice in the Description page of Project Settings.

#include "MCPSubsystem.h"
#include "Async/Future.h"
#include "IPythonScriptPlugin.h"
#include "MCPSetting.h"

#if REMOTE_MCP_WITH_NATIVE
#include "IModelContextProtocolModule.h"
#include "IModelContextProtocolTool.h"
#include "Interfaces/IPluginManager.h"
#include "ModelContextProtocolSession.h"
#include "Serialization/JsonSerializer.h"

DEFINE_LOG_CATEGORY_STATIC(LogRemoteMCPNative, Log, All);

namespace
{
	IModelContextProtocolModule* GetNativeMCPModule()
	{
		return FModuleManager::GetModulePtr<IModelContextProtocolModule>(TEXT("ModelContextProtocol"));
	}

	bool IsNativeMCPEnabled()
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("ModelContextProtocol"));
		return Plugin && Plugin->IsEnabled();
	}

	FString WriteJson(const TSharedRef<FJsonObject>& Object)
	{
		FString Json;
		FJsonSerializer::Serialize(Object, TJsonWriterFactory<>::Create(&Json));
		return Json;
	}

	template <typename RequestType>
	bool IsSameInvocation(const RequestType& Left, const RequestType& Right)
	{
		if constexpr (requires { Left.SessionId; Left.InvocationSerial; Left.InvocationId; })
		{
			const bool bHasIdentity = Left.InvocationId.IsValid() || (!Left.SessionId.IsEmpty() && Left.InvocationSerial != 0);
			return bHasIdentity && Left.SessionId == Right.SessionId
				&& Left.InvocationSerial == Right.InvocationSerial && Left.InvocationId == Right.InvocationId;
		}
		else
		{
			// A JSON-RPC request ID alone can refer to different calls in different sessions.
			return false;
		}
	}

	struct FRemoteMCPTool final : IModelContextProtocolTool
	{
		FString Name;
		FString Description;
		TSharedPtr<FJsonObject> InputSchema;
		TSharedPtr<FJsonObject> OutputSchema;
		TFunction<void(const FModelContextProtocolToolRequestId&, const TSharedPtr<FJsonObject>&, const FResultCallback&)> Invoke;
		TFunction<void(const FModelContextProtocolToolRequestId&)> Cancel;

		FString GetName() const override { return Name; }
		FString GetDescription() const override { return Description; }
		TSharedPtr<FJsonObject> GetInputJsonSchema() const override { return InputSchema; }
		TSharedPtr<FJsonObject> GetOutputJsonSchema() const override { return OutputSchema; }

		void RunAsync(const FModelContextProtocolToolRequestId& RequestId, const TSharedPtr<FJsonObject>& Params, const FResultCallback& OnComplete) override
		{
			Invoke(RequestId, Params, OnComplete);
		}

		void CancelAsync(const FModelContextProtocolToolRequestId& RequestId) override
		{
			Cancel(RequestId);
		}
	};
}

class FRemoteMCPNative : public TSharedFromThis<FRemoteMCPNative>
{
	using FResultCallback = IModelContextProtocolTool::FResultCallback;

	struct FPendingCall
	{
		FString ToolName;
		FModelContextProtocolToolRequestId RequestId;
		FResultCallback OnComplete;
	};

public:
	explicit FRemoteMCPNative(FMCPBridgeFuncDelegate& InBridge) : Bridge(InBridge) {}

	void Initialize(IModelContextProtocolModule& Module)
	{
		RefreshHandle = Module.OnRefreshTools().AddSP(AsShared(), &FRemoteMCPNative::RegisterTools);
	}

	bool Publish(const FString& ToolsJson)
	{
		TArray<TSharedPtr<FJsonValue>> Descriptors;
		if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ToolsJson), Descriptors) || !GetNativeMCPModule())
		{
			return false;
		}

		const TWeakPtr<FRemoteMCPNative> WeakBackend = AsShared();
		TArray<TSharedRef<IModelContextProtocolTool>> NewTools;
		for (const TSharedPtr<FJsonValue>& Descriptor : Descriptors)
		{
			const TSharedPtr<FJsonObject>* Fields;
			const TSharedPtr<FJsonObject>* Schema;
			const TSharedRef<FRemoteMCPTool> Tool = MakeShared<FRemoteMCPTool>();
			if (!Descriptor->TryGetObject(Fields) || !(*Fields)->TryGetStringField(TEXT("name"), Tool->Name)
				|| !(*Fields)->TryGetObjectField(TEXT("inputSchema"), Schema))
			{
				return false;
			}
			Tool->InputSchema = *Schema;
			if ((*Fields)->TryGetObjectField(TEXT("outputSchema"), Schema))
			{
				Tool->OutputSchema = *Schema;
			}
			(*Fields)->TryGetStringField(TEXT("description"), Tool->Description);
			Tool->Invoke = [WeakBackend, Name = Tool->Name](const auto& RequestId, const auto& Params, const FResultCallback& OnComplete)
			{
				if (const TSharedPtr<FRemoteMCPNative> Backend = WeakBackend.Pin())
				{
					Backend->Invoke(Name, RequestId, Params, OnComplete);
				}
				else
				{
					OnComplete(UE::ModelContextProtocol::MakeErrorResult(TEXT("RemoteMCP is stopped")));
				}
			};
			Tool->Cancel = [WeakBackend, Name = Tool->Name](const auto& RequestId)
			{
				if (const TSharedPtr<FRemoteMCPNative> Backend = WeakBackend.Pin())
				{
					Backend->Cancel(Name, RequestId);
				}
			};
			NewTools.Add(Tool);
		}

		UnregisterTools();
		Tools = MoveTemp(NewTools);
		RegisterTools();
		return true;
	}

	void Complete(const FString& CallId, const FString& ResultJson)
	{
		FPendingCall Call;
		if (!PendingCalls.RemoveAndCopyValue(CallId, Call))
		{
			return;
		}
		TSharedPtr<FJsonObject> Result;
		if (FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ResultJson), Result) && Result)
		{
			Call.OnComplete(FModelContextProtocolToolResult(Result));
		}
		else
		{
			Call.OnComplete(UE::ModelContextProtocol::MakeErrorResult(TEXT("RemoteMCP returned an invalid tool result")));
		}
	}

	void Stop()
	{
		bStopping = true;
		if (IModelContextProtocolModule* Module = GetNativeMCPModule())
		{
			Module->OnRefreshTools().Remove(RefreshHandle);
		}
		UnregisterTools();
		const auto Calls = MoveTemp(PendingCalls);
		for (const auto& Entry : Calls)
		{
			Entry.Value.OnComplete(UE::ModelContextProtocol::MakeErrorResult(TEXT("RemoteMCP is stopped")));
		}
	}

private:
	void RegisterTools()
	{
		if (IModelContextProtocolModule* Module = GetNativeMCPModule())
		{
			for (const TSharedRef<IModelContextProtocolTool>& Tool : Tools)
			{
				if (!Module->AddTool(Tool))
				{
					UE_LOG(LogRemoteMCPNative, Warning, TEXT("Unable to register native MCP tool %s"), *Tool->GetName());
				}
			}
		}
	}

	void UnregisterTools()
	{
		if (IModelContextProtocolModule* Module = GetNativeMCPModule())
		{
			for (const TSharedRef<IModelContextProtocolTool>& Tool : Tools)
			{
				Module->RemoveTool(Tool);
			}
		}
	}

	void Invoke(const FString& Name, const FModelContextProtocolToolRequestId& RequestId,
		const TSharedPtr<FJsonObject>& Params, const FResultCallback& OnComplete)
	{
		if (bStopping || !Bridge.IsBound())
		{
			OnComplete(UE::ModelContextProtocol::MakeErrorResult(TEXT("RemoteMCP is stopped")));
			return;
		}
		const FString CallId = FGuid::NewGuid().ToString();
		PendingCalls.Add(CallId, {Name, RequestId, OnComplete});
		const TSharedRef<FJsonObject> Message = MakeShared<FJsonObject>();
		Message->SetStringField(TEXT("id"), CallId);
		Message->SetStringField(TEXT("name"), Name);
		Message->SetObjectField(TEXT("arguments"), Params ? Params : MakeShared<FJsonObject>());
		if (!Bridge.Execute(EMCPBridgeFuncType::InvokeNative, WriteJson(Message)))
		{
			Complete(CallId, FString());
		}
	}

	void Cancel(const FString& Name, const FModelContextProtocolToolRequestId& RequestId)
	{
		for (const auto& Entry : PendingCalls)
		{
			const FPendingCall& Call = Entry.Value;
			if (Call.ToolName == Name && IsSameInvocation(Call.RequestId, RequestId) && Bridge.IsBound())
			{
				Bridge.Execute(EMCPBridgeFuncType::CancelNative, Entry.Key);
				return;
			}
		}
	}

	FMCPBridgeFuncDelegate& Bridge;
	FDelegateHandle RefreshHandle;
	TArray<TSharedRef<IModelContextProtocolTool>> Tools;
	TMap<FString, FPendingCall> PendingCalls;
	bool bStopping = false;
};
#endif

UMCPSubsystem* UMCPSubsystem::Instance = nullptr;

namespace
{
	void ResetMCPObject(FMCPObject& Context)
	{
		Context.Bridge.Unbind();
		Context.Tick.Unbind();
		Context.GUID.Reset();
		Context.PythonObjectHandle = nullptr;
	}
}

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

void UMCPSubsystem::Deinitialize()
{
	StopMCP();
	ClearObject();
}

void UMCPSubsystem::PostEngineInit()
{
#if ENGINE_MAJOR_VERSION > 5 || ENGINE_MINOR_VERSION >= 7
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

void UMCPSubsystem::Initialize()
{
	UMCPSubsystem::PostEngineInit();
}

UMCPSubsystem* UMCPSubsystem::Get()
{
	return Instance;
}

void UMCPSubsystem::SetupObject(FMCPObject Context)
{
	ResetMCPObject(MCPContext);
	this->MCPContext = Context;
	WaitStart = true;
}

void UMCPSubsystem::ClearObject()
{
	ResetMCPObject(MCPContext);
	WaitStart = false;
}

void UMCPSubsystem::StartMCP()
{
	// StopMCP();
	if (MCPContext.IsRunning())
	{
		UE_LOG(LogTemp, Error, TEXT("MCP Already Running"));
		return;
	}

	SetupBridge();
#if REMOTE_MCP_WITH_NATIVE
	if (MCPContext.Valid() && IsNativeMCPEnabled())
	{
		if (IModelContextProtocolModule* Module = GetNativeMCPModule())
		{
			NativeMCP = MakeShared<FRemoteMCPNative>(MCPContext.Bridge);
			NativeMCP->Initialize(*Module);
			if (MCPContext.Bridge.Execute(EMCPBridgeFuncType::StartNative, FString()))
			{
				UE_LOG(LogRemoteMCPNative, Log, TEXT("RemoteMCP tools registered with Unreal MCP"));
				return;
			}
			NativeMCP->Stop();
			NativeMCP.Reset();
		}
		UE_LOG(LogRemoteMCPNative, Error, TEXT("Failed to initialize RemoteMCP with Unreal MCP"));
		ClearObject();
		return;
	}
#endif
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
#if REMOTE_MCP_WITH_NATIVE
	if (NativeMCP)
	{
		NativeMCP->Stop();
		NativeMCP.Reset();
		if (MCPContext.Bridge.IsBound())
		{
			MCPContext.Bridge.Execute(EMCPBridgeFuncType::Exit, TEXT("MCP Stopped"));
		}
		ClearObject();
		return;
	}
#endif
	if (!MCPContext.Bridge.IsBound())
	{
		ClearObject();
		return;
	}

	if (!MCPContext.IsRunning())
	{
		ClearObject();
		return;
	}
	if (MCPContext.Bridge.IsBound())
	{
		auto _ = MCPContext.Bridge.Execute(EMCPBridgeFuncType::Exit, TEXT("MCP Stopped"));
		RunTread.WaitFor(FTimespan::FromSeconds(100));
	}

	ClearObject();
}

bool UMCPSubsystem::PublishNativeTools(const FString& ToolsJson)
{
#if REMOTE_MCP_WITH_NATIVE
	return NativeMCP && NativeMCP->Publish(ToolsJson);
#else
	return false;
#endif
}

void UMCPSubsystem::CompleteNativeTool(const FString& CallId, const FString& ResultJson)
{
#if REMOTE_MCP_WITH_NATIVE
	if (const TSharedPtr<FRemoteMCPNative> Backend = NativeMCP)
	{
		Backend->Complete(CallId, ResultJson);
	}
#endif
}

EMCPServerState UMCPSubsystem::GetMCPServeState() const
{
	if (MCPContext.Valid())
	{
		return EMCPServerState::Runing;
	}
	return EMCPServerState::Stop;
}
