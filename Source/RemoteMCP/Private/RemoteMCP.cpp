// Copyright Epic Games, Inc. All Rights Reserved.

#include "RemoteMCP.h"


#include "EditorUtilityWidgetBlueprint.h"
#include "MCPSubsystem.h"
#include "RemoteMCPStyle.h"
#include "RemoteMCPCommands.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"
#include "MCPMisc.h"

class UEditorUtilitySubsystem;
class UEditorUtilityWidget;
static const FName RemoteMCPTabName("RemoteMCP");

#define LOCTEXT_NAMESPACE "FRemoteMCPModule"
DEFINE_LOG_CATEGORY(LogRemoteMCP);


namespace MCPCommand
{
	static FAutoConsoleCommand StartMCPCommand{
		TEXT("MCP.Start"),
		TEXT("Start RemoteMCP"),
		FConsoleCommandDelegate::CreateLambda([]()
		{
			if (GEditor)
			{
				if (UMCPSubsystem* EditorUtilitySubsystem = GEditor->GetEditorSubsystem<UMCPSubsystem>())
				{
					EditorUtilitySubsystem->StartMCP();
				}
			}
		}),

	};

	static FAutoConsoleCommand StopMCPCommand{
		TEXT("MCP.Stop"),
		TEXT("Stop RemoteMCP"),
		FConsoleCommandDelegate::CreateLambda([]()
		{
			if (GEditor)
			{
				if (UMCPSubsystem* McpSubsystem = GEditor->GetEditorSubsystem<UMCPSubsystem>())
				{
					McpSubsystem->StopMCP();
				}
			}
		})
	};

	static FAutoConsoleCommand RestartMCPCommand{
		TEXT("MCP.Restart"),
		TEXT("Restart RemoteMCP"),
		FConsoleCommandDelegate::CreateLambda([]()
		{
			if (GEditor)
			{
				if (UMCPSubsystem* McpSubsystem = GEditor->GetEditorSubsystem<UMCPSubsystem>())
				{
					McpSubsystem->StopMCP();
					McpSubsystem->StartMCP();
				}
			}
		})
	};

	static FAutoConsoleCommand MCPStateCommand{
		TEXT("MCP.State"),
		TEXT("Get RemoteMCP State"),
		FConsoleCommandDelegate::CreateLambda([]()
		{
			if (GEditor)
			{
				if (UMCPSubsystem* McpSubsystem = GEditor->GetEditorSubsystem<UMCPSubsystem>())
				{
					auto State = McpSubsystem->GetMCPServeState();
					switch (State)
					{
					case EMCPServerState::Runing:
						UE_LOG(LogRemoteMCP, Log, TEXT("RemoteMCP Running"));
						break;
					case EMCPServerState::Stop:
						UE_LOG(LogRemoteMCP, Log, TEXT("RemoteMCP Stopped"));
						break;
					default:
						break;
					}
				}
			}
		})
	};

	static FAutoConsoleCommand MCPDebugPanel{
		TEXT("MCP.DebugPanel"),
		TEXT("open debug panel whitch only for developer(and is in beta)"),
		FConsoleCommandDelegate::CreateLambda([]()
		{
			FGlobalTabmanager::Get()->TryInvokeTab(RemoteMCPTabName);
		})
	};
}

void FRemoteMCPModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	
	FRemoteMCPStyle::Initialize();
	FRemoteMCPStyle::ReloadTextures();

	FRemoteMCPCommands::Register();
	
	PluginCommands = MakeShareable(new FUICommandList);

	PluginCommands->MapAction(
		FRemoteMCPCommands::Get().OpenPluginWindow,
		FExecuteAction::CreateRaw(this, &FRemoteMCPModule::PluginButtonClicked),
		FCanExecuteAction());

	//UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FRemoteMCPModule::RegisterMenus));
	
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(RemoteMCPTabName, FOnSpawnTab::CreateRaw(this, &FRemoteMCPModule::OnSpawnPluginTab))
		.SetDisplayName(LOCTEXT("FRemoteMCPTabTitle", "RemoteMCP"))
		.SetMenuType(ETabSpawnerMenuType::Hidden);

	//RegisterCommand();
}

void FRemoteMCPModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FRemoteMCPStyle::Shutdown();

	FRemoteMCPCommands::Unregister();

	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(RemoteMCPTabName);
}

TSharedRef<SDockTab> FRemoteMCPModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
	FText WidgetText = FText::Format(
		LOCTEXT("WindowWidgetText", "Add code to {0} in {1} to override this window's contents"),
		FText::FromString(TEXT("FRemoteMCPModule::OnSpawnPluginTab")),
		FText::FromString(TEXT("RemoteMCP.cpp"))
		);

	auto WidgetClass = LoadObject<UEditorUtilityWidgetBlueprint>(nullptr,TEXT("/RemoteMCP/EditorUI/MainPanel"));
	return WidgetClass->SpawnEditorUITab(SpawnTabArgs);
}

void FRemoteMCPModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(RemoteMCPTabName);
}

void FRemoteMCPModule::RegisterMenus()
{
	// Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
	FToolMenuOwnerScoped OwnerScoped(this);

	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
		{
			FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
			Section.AddMenuEntryWithCommandList(FRemoteMCPCommands::Get().OpenPluginWindow, PluginCommands);
		}
	}

	{
		UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
		{
			FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("Settings");
			{
				FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FRemoteMCPCommands::Get().OpenPluginWindow));
				Entry.SetCommandList(PluginCommands);
			}
		}
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FRemoteMCPModule, RemoteMCP)