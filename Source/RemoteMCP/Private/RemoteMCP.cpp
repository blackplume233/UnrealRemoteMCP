// Copyright Epic Games, Inc. All Rights Reserved.

#include "RemoteMCP.h"


#include "EditorUtilityWidgetBlueprint.h"
#include "RemoteMCPStyle.h"
#include "RemoteMCPCommands.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"

class UEditorUtilitySubsystem;
class UEditorUtilityWidget;
static const FName RemoteMCPTabName("RemoteMCP");

#define LOCTEXT_NAMESPACE "FRemoteMCPModule"

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

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FRemoteMCPModule::RegisterMenus));
	
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(RemoteMCPTabName, FOnSpawnTab::CreateRaw(this, &FRemoteMCPModule::OnSpawnPluginTab))
		.SetDisplayName(LOCTEXT("FRemoteMCPTabTitle", "RemoteMCP"))
		.SetMenuType(ETabSpawnerMenuType::Hidden);
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