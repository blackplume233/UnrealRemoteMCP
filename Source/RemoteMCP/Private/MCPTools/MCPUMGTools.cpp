// Fill out your copyright notice in the Description page of Project Settings.


#include "MCPTools/MCPUMGTools.h"
#include "MCPTools/UnrealMCPCommonUtils.h"
#include "Editor.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "WidgetBlueprint.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/PanelWidget.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "K2Node_Event.h"

static UWidgetBlueprint* FindWidgetBlueprintByName(const FString& Name)
{
	if (Name.StartsWith(TEXT("/")))
	{
		return Cast<UWidgetBlueprint>(UEditorAssetLibrary::LoadAsset(Name));
	}

	FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	TArray<FAssetData> Assets;
	ARM.Get().GetAssetsByClass(UWidgetBlueprint::StaticClass()->GetClassPathName(), Assets);
	for (const FAssetData& Asset : Assets)
	{
		if (Asset.AssetName.ToString() == Name)
		{
			return Cast<UWidgetBlueprint>(Asset.GetAsset());
		}
	}
	return nullptr;
}


FJsonObjectParameter UMCPUMGTools::HandleCreateUMGWidgetBlueprint(const FJsonObjectParameter& Params)
{
	// Get required parameters
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("name"), BlueprintName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
	}

	FString PackagePath;
	if (!Params->TryGetStringField(TEXT("path"), PackagePath))
	{
		PackagePath = TEXT("/Game/Widgets");
	}
	if (!PackagePath.EndsWith(TEXT("/")))
	{
		PackagePath += TEXT("/");
	}
	FString AssetName = BlueprintName;
	FString FullPath = PackagePath + AssetName;

	// Check if asset already exists
	if (UEditorAssetLibrary::DoesAssetExist(FullPath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Widget Blueprint '%s' already exists"), *BlueprintName));
	}

	// Create package
	UPackage* Package = CreatePackage(*FullPath);
	if (!Package)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create package"));
	}

	// Create Widget Blueprint using KismetEditorUtilities
	UBlueprint* NewBlueprint = FKismetEditorUtilities::CreateBlueprint(
		UUserWidget::StaticClass(),  // Parent class
		Package,                     // Outer package
		FName(*AssetName),           // Blueprint name
		BPTYPE_Normal,               // Blueprint type
		UBlueprint::StaticClass(),   // Blueprint class
		UBlueprintGeneratedClass::StaticClass(), // Generated class
		FName("CreateUMGWidget")     // Creation method name
	);

	// Make sure the Blueprint was created successfully
	UWidgetBlueprint* WidgetBlueprint = Cast<UWidgetBlueprint>(NewBlueprint);
	if (!WidgetBlueprint)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create Widget Blueprint"));
	}

	// Add a default Canvas Panel if one doesn't exist
	if (!WidgetBlueprint->WidgetTree->RootWidget)
	{
		UCanvasPanel* RootCanvas = WidgetBlueprint->WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
		WidgetBlueprint->WidgetTree->RootWidget = RootCanvas;
	}

	// Mark the package dirty and notify asset registry
	Package->MarkPackageDirty();
	FAssetRegistryModule::AssetCreated(WidgetBlueprint);

	// Compile the blueprint
	FKismetEditorUtilities::CompileBlueprint(WidgetBlueprint);

	// Create success response
	FJsonObjectParameter ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("name"), BlueprintName);
	ResultObj->SetStringField(TEXT("path"), FullPath);
	return ResultObj;
}

FJsonObjectParameter UMCPUMGTools::HandleAddWidgetToViewport(const FJsonObjectParameter& Params)
{
	// Get required parameters
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
	}

	UWidgetBlueprint* WidgetBlueprint = FindWidgetBlueprintByName(BlueprintName);
	if (!WidgetBlueprint)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Widget Blueprint '%s' not found"), *BlueprintName));
	}

	// Get optional Z-order parameter
	int32 ZOrder = 0;
	Params->TryGetNumberField(TEXT("z_order"), ZOrder);

	// Create widget instance
	UClass* WidgetClass = WidgetBlueprint->GeneratedClass;
	if (!WidgetClass)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get widget class"));
	}

	// Note: This creates the widget but doesn't add it to viewport
	// The actual addition to viewport should be done through Blueprint nodes
	// as it requires a game context

	// Create success response with instructions
	FJsonObjectParameter ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("blueprint_name"), BlueprintName);
	ResultObj->SetStringField(TEXT("class_path"), WidgetClass->GetPathName());
	ResultObj->SetNumberField(TEXT("z_order"), ZOrder);
	ResultObj->SetStringField(TEXT("note"), TEXT("Widget class ready. Use CreateWidget and AddToViewport nodes in Blueprint to display in game."));
	return ResultObj;
}

FJsonObjectParameter UMCPUMGTools::HandleBindWidgetEvent(const FJsonObjectParameter& Params)
{
	FJsonObjectParameter Response = MakeShared<FJsonObject>();

	// Get required parameters
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
	{
		Response->SetStringField(TEXT("error"), TEXT("Missing blueprint_name parameter"));
		return Response;
	}

	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		Response->SetStringField(TEXT("error"), TEXT("Missing widget_name parameter"));
		return Response;
	}

	FString EventName;
	if (!Params->TryGetStringField(TEXT("event_name"), EventName))
	{
		Response->SetStringField(TEXT("error"), TEXT("Missing event_name parameter"));
		return Response;
	}

	UWidgetBlueprint* WidgetBlueprint = FindWidgetBlueprintByName(BlueprintName);
	if (!WidgetBlueprint)
	{
		Response->SetStringField(TEXT("error"), FString::Printf(TEXT("Widget Blueprint '%s' not found"), *BlueprintName));
		return Response;
	}

	// Create the event graph if it doesn't exist
	UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(WidgetBlueprint);
	if (!EventGraph)
	{
		Response->SetStringField(TEXT("error"), TEXT("Failed to find or create event graph"));
		return Response;
	}

	// Find the widget in the blueprint
	UWidget* Widget = WidgetBlueprint->WidgetTree->FindWidget(*WidgetName);
	if (!Widget)
	{
		Response->SetStringField(TEXT("error"), FString::Printf(TEXT("Failed to find widget: %s"), *WidgetName));
		return Response;
	}

	// Create the event node (e.g., OnClicked for buttons)
	UK2Node_Event* EventNode = nullptr;

	// Find existing nodes first
	TArray<UK2Node_Event*> AllEventNodes;
	FBlueprintEditorUtils::GetAllNodesOfClass<UK2Node_Event>(WidgetBlueprint, AllEventNodes);

	for (UK2Node_Event* Node : AllEventNodes)
	{
		if (Node->CustomFunctionName == FName(*EventName) && Node->EventReference.GetMemberParentClass() == Widget->GetClass())
		{
			EventNode = Node;
			break;
		}
	}

	// If no existing node, create a new one
	if (!EventNode)
	{
		// Calculate position - place it below existing nodes
		float MaxHeight = 0.0f;
		for (UEdGraphNode* Node : EventGraph->Nodes)
		{
			MaxHeight = FMath::Max(MaxHeight, Node->NodePosY);
		}

		const FVector2D NodePos(200, MaxHeight + 200);

		// Call CreateNewBoundEventForClass, which returns void, so we can't capture the return value directly
		// We'll need to find the node after creating it
		FKismetEditorUtilities::CreateNewBoundEventForClass(
			Widget->GetClass(),
			FName(*EventName),
			WidgetBlueprint,
			nullptr  // We don't need a specific property binding
		);

		// Now find the newly created node
		TArray<UK2Node_Event*> UpdatedEventNodes;
		FBlueprintEditorUtils::GetAllNodesOfClass<UK2Node_Event>(WidgetBlueprint, UpdatedEventNodes);

		for (UK2Node_Event* Node : UpdatedEventNodes)
		{
			if (Node->CustomFunctionName == FName(*EventName) && Node->EventReference.GetMemberParentClass() == Widget->GetClass())
			{
				EventNode = Node;

				// Set position of the node
				EventNode->NodePosX = NodePos.X;
				EventNode->NodePosY = NodePos.Y;

				break;
			}
		}
	}

	if (!EventNode)
	{
		Response->SetStringField(TEXT("error"), TEXT("Failed to create event node"));
		return Response;
	}

	FKismetEditorUtilities::CompileBlueprint(WidgetBlueprint);

	Response->SetBoolField(TEXT("success"), true);
	Response->SetStringField(TEXT("event_name"), EventName);
	return Response;
}

FJsonObjectParameter UMCPUMGTools::HandleClearWidgetTree(const FJsonObjectParameter& Params)
{
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
	}

	UWidgetBlueprint* WidgetBlueprint = FindWidgetBlueprintByName(BlueprintName);
	if (!WidgetBlueprint)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Widget Blueprint '%s' not found"), *BlueprintName));
	}

	UWidgetTree* WidgetTree = WidgetBlueprint->WidgetTree;
	WidgetTree->RootWidget = nullptr;

	UCanvasPanel* RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
	WidgetTree->RootWidget = RootCanvas;

	WidgetBlueprint->MarkPackageDirty();
	FKismetEditorUtilities::CompileBlueprint(WidgetBlueprint);

	FJsonObjectParameter ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("blueprint_name"), BlueprintName);
	return ResultObj;
}

// ===== Generic Widget Helpers =====

static UClass* FindWidgetClassByName(const FString& TypeName)
{
	FString SearchName = TypeName;
	if (SearchName.Len() > 1 && SearchName.StartsWith(TEXT("U")) && FChar::IsUpper(SearchName[1]))
	{
		SearchName.RightChopInline(1);
	}

	UClass* Found = FindFirstObject<UClass>(*SearchName, EFindFirstObjectOptions::NativeFirst, ELogVerbosity::NoLogging);
	if (Found && Found->IsChildOf(UWidget::StaticClass()))
	{
		return Found;
	}

	Found = StaticLoadClass(UWidget::StaticClass(), nullptr, *TypeName);
	if (Found)
	{
		return Found;
	}

	for (TObjectIterator<UClass> It; It; ++It)
	{
		if (It->IsChildOf(UWidget::StaticClass()) && It->GetName() == SearchName)
		{
			return *It;
		}
	}

	return nullptr;
}

static bool SetPropertyFromJsonValue(UObject* Obj, const FString& PropName, const TSharedPtr<FJsonValue>& JsonVal)
{
	FProperty* Prop = Obj->GetClass()->FindPropertyByName(*PropName);
	if (!Prop)
	{
		return false;
	}

	void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Obj);

	if (CastField<FTextProperty>(Prop))
	{
		CastField<FTextProperty>(Prop)->SetPropertyValue(ValuePtr, FText::FromString(JsonVal->AsString()));
		return true;
	}

	FString Str;
	if (JsonVal->Type == EJson::String)
	{
		Str = JsonVal->AsString();
	}
	else if (JsonVal->Type == EJson::Number)
	{
		Str = FString::SanitizeFloat(JsonVal->AsNumber());
	}
	else if (JsonVal->Type == EJson::Boolean)
	{
		Str = JsonVal->AsBool() ? TEXT("True") : TEXT("False");
	}
	else
	{
		return false;
	}

	return Prop->ImportText_Direct(*Str, ValuePtr, Obj, 0) != nullptr;
}

static TSharedPtr<FJsonObject> BuildWidgetTreeJson(UWidget* Widget)
{
	if (!Widget)
	{
		return nullptr;
	}

	TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
	Obj->SetStringField(TEXT("name"), Widget->GetName());
	Obj->SetStringField(TEXT("type"), Widget->GetClass()->GetName());
	Obj->SetStringField(TEXT("path"), Widget->GetPathName());
	Obj->SetBoolField(TEXT("visible"), Widget->IsVisible());

	if (UPanelSlot* Slot = Widget->Slot)
	{
		TSharedPtr<FJsonObject> SlotJson = MakeShared<FJsonObject>();
		SlotJson->SetStringField(TEXT("type"), Slot->GetClass()->GetName());

		if (UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(Slot))
		{
			FVector2D Pos = CS->GetPosition();
			FVector2D Size = CS->GetSize();
			FAnchors Anc = CS->GetAnchors();

			TArray<TSharedPtr<FJsonValue>> PosArr;
			PosArr.Add(MakeShared<FJsonValueNumber>(Pos.X));
			PosArr.Add(MakeShared<FJsonValueNumber>(Pos.Y));
			SlotJson->SetArrayField(TEXT("position"), PosArr);

			TArray<TSharedPtr<FJsonValue>> SizeArr;
			SizeArr.Add(MakeShared<FJsonValueNumber>(Size.X));
			SizeArr.Add(MakeShared<FJsonValueNumber>(Size.Y));
			SlotJson->SetArrayField(TEXT("size"), SizeArr);

			TArray<TSharedPtr<FJsonValue>> AncArr;
			AncArr.Add(MakeShared<FJsonValueNumber>(Anc.Minimum.X));
			AncArr.Add(MakeShared<FJsonValueNumber>(Anc.Minimum.Y));
			AncArr.Add(MakeShared<FJsonValueNumber>(Anc.Maximum.X));
			AncArr.Add(MakeShared<FJsonValueNumber>(Anc.Maximum.Y));
			SlotJson->SetArrayField(TEXT("anchors"), AncArr);
		}

		Obj->SetObjectField(TEXT("slot"), SlotJson);
	}

	if (UPanelWidget* Panel = Cast<UPanelWidget>(Widget))
	{
		TArray<TSharedPtr<FJsonValue>> Children;
		for (int32 i = 0; i < Panel->GetChildrenCount(); i++)
		{
			TSharedPtr<FJsonObject> ChildJson = BuildWidgetTreeJson(Panel->GetChildAt(i));
			if (ChildJson.IsValid())
			{
				Children.Add(MakeShared<FJsonValueObject>(ChildJson));
			}
		}
		if (Children.Num() > 0)
		{
			Obj->SetArrayField(TEXT("children"), Children);
		}
		Obj->SetNumberField(TEXT("child_count"), Panel->GetChildrenCount());
	}

	return Obj;
}

// ===== Generic CRUD Handlers =====

FJsonObjectParameter UMCPUMGTools::HandleAddWidget(const FJsonObjectParameter& Params)
{
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name'"));
	}

	FString WidgetType;
	if (!Params->TryGetStringField(TEXT("widget_type"), WidgetType))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_type'"));
	}

	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_name'"));
	}

	UWidgetBlueprint* WB = FindWidgetBlueprintByName(BlueprintName);
	if (!WB)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint '%s' not found"), *BlueprintName));
	}

	UClass* WidgetClass = FindWidgetClassByName(WidgetType);
	if (!WidgetClass)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Widget class '%s' not found"), *WidgetType));
	}

	if (!WB->WidgetTree->RootWidget)
	{
		UCanvasPanel* Root = WB->WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
		WB->WidgetTree->RootWidget = Root;
	}

	UWidget* NewWidget = WB->WidgetTree->ConstructWidget<UWidget>(WidgetClass, *WidgetName);
	if (!NewWidget)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("ConstructWidget failed"));
	}

	const TSharedPtr<FJsonObject>* PropsObj;
	if (Params->TryGetObjectField(TEXT("properties"), PropsObj))
	{
		for (const auto& KV : (*PropsObj)->Values)
		{
			SetPropertyFromJsonValue(NewWidget, KV.Key, KV.Value);
		}
	}

	UPanelWidget* Parent = nullptr;
	FString ParentName;
	if (Params->TryGetStringField(TEXT("parent_name"), ParentName))
	{
		Parent = Cast<UPanelWidget>(WB->WidgetTree->FindWidget(*ParentName));
		if (!Parent)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(
				FString::Printf(TEXT("Parent '%s' not found or not a PanelWidget"), *ParentName));
		}
	}
	if (!Parent)
	{
		Parent = Cast<UPanelWidget>(WB->WidgetTree->RootWidget);
	}

	UPanelSlot* Slot = Parent->AddChild(NewWidget);
	if (!Slot)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("AddChild failed (parent may be full or incompatible)"));
	}

	const TSharedPtr<FJsonObject>* SlotObj;
	if (Params->TryGetObjectField(TEXT("slot"), SlotObj))
	{
		for (const auto& KV : (*SlotObj)->Values)
		{
			SetPropertyFromJsonValue(Slot, KV.Key, KV.Value);
		}
	}

	if (UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(Slot))
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr;
		if (Params->TryGetArrayField(TEXT("position"), Arr) && Arr->Num() >= 2)
		{
			CS->SetPosition(FVector2D((*Arr)[0]->AsNumber(), (*Arr)[1]->AsNumber()));
		}
		if (Params->TryGetArrayField(TEXT("size"), Arr) && Arr->Num() >= 2)
		{
			CS->SetSize(FVector2D((*Arr)[0]->AsNumber(), (*Arr)[1]->AsNumber()));
		}
	}

	WB->MarkPackageDirty();
	FKismetEditorUtilities::CompileBlueprint(WB);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("success"), true);
	Result->SetStringField(TEXT("widget_name"), WidgetName);
	Result->SetStringField(TEXT("widget_type"), WidgetClass->GetName());
	Result->SetStringField(TEXT("parent"), Parent->GetName());
	return Result;
}

FJsonObjectParameter UMCPUMGTools::HandleRemoveWidget(const FJsonObjectParameter& Params)
{
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name'"));
	}

	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_name'"));
	}

	UWidgetBlueprint* WB = FindWidgetBlueprintByName(BlueprintName);
	if (!WB)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Blueprint '%s' not found"), *BlueprintName));
	}

	UWidget* Widget = WB->WidgetTree->FindWidget(*WidgetName);
	if (!Widget)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Widget '%s' not found"), *WidgetName));
	}

	if (Widget == WB->WidgetTree->RootWidget)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			TEXT("Cannot remove root widget; use clear_widget_tree instead"));
	}

	if (UPanelWidget* ParentPanel = Widget->GetParent())
	{
		ParentPanel->RemoveChild(Widget);
	}

	WB->WidgetTree->Modify();
	WB->MarkPackageDirty();
	FKismetEditorUtilities::CompileBlueprint(WB);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("success"), true);
	Result->SetStringField(TEXT("removed"), WidgetName);
	return Result;
}

FJsonObjectParameter UMCPUMGTools::HandleGetWidgetTree(const FJsonObjectParameter& Params)
{
	FString BlueprintName;
	if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name'"));
	}

	UWidgetBlueprint* WB = FindWidgetBlueprintByName(BlueprintName);
	if (!WB)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Blueprint '%s' not found"), *BlueprintName));
	}

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("blueprint_path"), WB->GetPathName());

	FString WidgetName;
	if (Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		UWidget* Found = WB->WidgetTree->FindWidget(*WidgetName);
		if (!Found)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(
				FString::Printf(TEXT("Widget '%s' not found"), *WidgetName));
		}
		Result->SetObjectField(TEXT("widget"), BuildWidgetTreeJson(Found));
		return Result;
	}

	if (WB->WidgetTree->RootWidget)
	{
		Result->SetObjectField(TEXT("root"), BuildWidgetTreeJson(WB->WidgetTree->RootWidget));
	}
	else
	{
		Result->SetStringField(TEXT("root"), TEXT("null"));
	}

	return Result;
}