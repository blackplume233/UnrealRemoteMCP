// Copyright Epic Games, Inc. All Rights Reserved.

using System.IO;
using UnrealBuildTool;

public class RemoteMCP : ModuleRules
{
	public RemoteMCP(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		// Use the optional engine plugin through its virtual interface, without linking to its DLL.
		string McpSource = Path.Combine(EngineDirectory, "Plugins", "Experimental", "ModelContextProtocol", "Source", "ModelContextProtocol");
		bool HasNativeMcp = File.Exists(Path.Combine(McpSource, "Public", "IModelContextProtocolModule.h"));
		PrivateDefinitions.Add(HasNativeMcp ? "REMOTE_MCP_WITH_NATIVE=1" : "REMOTE_MCP_WITH_NATIVE=0");
		if (HasNativeMcp)
		{
			PrivateIncludePathModuleNames.Add("ModelContextProtocol");
		}
		
		PublicIncludePaths.AddRange(
			new string[] {
				// ... add public include paths required here ...
			}
			);
				
		
		PrivateIncludePaths.AddRange(
			new string[] {
				// ... add other private include paths required here ...
			}
			);
			
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core", "JsonUtilities",
				// ... add other public dependencies that you statically link with here ...
			}
			);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"Projects",
				"InputCore",
				"EditorFramework",
				"UnrealEd",
				"ToolMenus",
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore", "Blutility","UMG","UMGEditor", "PythonScriptPlugin","Json","JsonUtilities"
				// ... add private dependencies that you statically link with here ...	
				,"DeveloperSettings", "EditorScriptingUtilities",
				"AIModule", "BehaviorTreeEditor", "AIGraph"
			}
			);
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"UnrealEd",
				"EditorScriptingUtilities",
				"EditorSubsystem",
				"Slate",
				"SlateCore",
				"UMG",
				"Kismet",
				"KismetCompiler",
				"BlueprintGraph",
				"Projects",
				"AssetRegistry"
			}
		);
		
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				// ... add any modules that your module loads dynamically here ...
			}
			);
	}
}
