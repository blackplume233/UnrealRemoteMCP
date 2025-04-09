// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Framework/Commands/Commands.h"
#include "RemoteMCPStyle.h"

class FRemoteMCPCommands : public TCommands<FRemoteMCPCommands>
{
public:

	FRemoteMCPCommands()
		: TCommands<FRemoteMCPCommands>(TEXT("RemoteMCP"), NSLOCTEXT("Contexts", "RemoteMCP", "RemoteMCP Plugin"), NAME_None, FRemoteMCPStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > OpenPluginWindow;
};