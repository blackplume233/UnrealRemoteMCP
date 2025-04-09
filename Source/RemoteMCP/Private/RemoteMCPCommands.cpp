// Copyright Epic Games, Inc. All Rights Reserved.

#include "RemoteMCPCommands.h"

#define LOCTEXT_NAMESPACE "FRemoteMCPModule"

void FRemoteMCPCommands::RegisterCommands()
{
	UI_COMMAND(OpenPluginWindow, "RemoteMCP", "Bring up RemoteMCP window", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
