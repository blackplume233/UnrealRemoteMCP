#include "MCPTools/MCPBehaviorTreeTools.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTreeGraph.h"
#include "BehaviorTreeGraphNode.h"
#include "BehaviorTreeGraphNode_Service.h"
#include "BehaviorTreeGraphNode_Composite.h"
#include "BehaviorTreeGraphNode_Task.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EditorAssetLibrary.h"
#include "BehaviorTreeFactory.h"
#include "MCPTools/UnrealMCPCommonUtils.h"
#include "Dom/JsonObject.h"
#include "AIGraphNode.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BehaviorTree/BTService.h"
#include "BehaviorTree/BTCompositeNode.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/Tasks/BTTask_Wait.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "Editor.h"

FJsonObjectParameter UMCPBehaviorTreeTools::HandleGetBehaviorTreeGraph(const FJsonObjectParameter& Params)
{
    // AI(GPT-5.2): 复用已存在 UFUNCTION 作为扩展入口（避免 LiveCoding 新增 UFUNCTION 需重启）
    // - op == "set_blackboard": 设置 BehaviorTree.BlackboardAsset
	// - op == "get_blackboard": 读取 BehaviorTree.BlackboardAsset
    FString Op;
	if (Params->TryGetStringField(TEXT("op"), Op) && Op.Equals(TEXT("get_blackboard"), ESearchCase::IgnoreCase))
	{
		FString BTPath;
		if (!Params->TryGetStringField(TEXT("bt_path"), BTPath))
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'bt_path' parameter"));
		}
		UBehaviorTree* BT = LoadObject<UBehaviorTree>(nullptr, *BTPath);
		if (!BT)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Behavior Tree not found: %s"), *BTPath));
		}

		TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
		ResultObj->SetStringField(TEXT("bt_path"), BT->GetPathName());
		ResultObj->SetStringField(TEXT("bb_path"), BT->BlackboardAsset ? BT->BlackboardAsset->GetPathName() : TEXT(""));
		return FUnrealMCPCommonUtils::CreateSuccessResponse(ResultObj);
	}
    if (Params->TryGetStringField(TEXT("op"), Op) && Op.Equals(TEXT("set_blackboard"), ESearchCase::IgnoreCase))
    {
        FString BTPath;
        FString BBPath;
        if (!Params->TryGetStringField(TEXT("bt_path"), BTPath))
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'bt_path' parameter"));
        }
        if (!Params->TryGetStringField(TEXT("bb_path"), BBPath))
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'bb_path' parameter"));
        }

        UBehaviorTree* BT = LoadObject<UBehaviorTree>(nullptr, *BTPath);
        if (!BT)
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Behavior Tree not found: %s"), *BTPath));
        }
        UBlackboardData* BB = LoadObject<UBlackboardData>(nullptr, *BBPath);
        if (!BB)
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blackboard not found: %s"), *BBPath));
        }

        BT->Modify();
        BT->BlackboardAsset = BB;
        BT->MarkPackageDirty();

        TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
        ResultObj->SetStringField(TEXT("bt_path"), BT->GetPathName());
        ResultObj->SetStringField(TEXT("bb_path"), BB->GetPathName());
        return FUnrealMCPCommonUtils::CreateSuccessResponse(ResultObj);
    }

    FString BTPath;
    if (!Params->TryGetStringField(TEXT("bt_path"), BTPath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'bt_path' parameter"));
    }

    UBehaviorTree* BT = LoadObject<UBehaviorTree>(nullptr, *BTPath);
    UE_LOG(LogTemp, Display, TEXT("HandleGetBehaviorTreeGraph called for: %s"), *BTPath);
    if (!BT)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Behavior Tree not found: %s"), *BTPath));
    }

    UEdGraph* Graph = nullptr;
    TArray<UObject*> SubObjects;
    GetObjectsWithOuter(BT, SubObjects);
    for (UObject* Obj : SubObjects)
    {
        if (Obj && Obj->IsA<UBehaviorTreeGraph>())
        {
            Graph = Cast<UEdGraph>(Obj);
            break;
        }
    }

    // AI(GPT-5.2): 自动确保 Graph 存在（新建 BT 资产时，Graph 可能尚未生成）
    // 经验：打开一次资产编辑器通常会触发创建 BTGraph / BehaviorTreeGraph 子对象。
    if (!Graph)
    {
#if WITH_EDITOR
        if (GEditor)
        {
            if (UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
            {
                AssetEditorSubsystem->OpenEditorForAsset(BT);
            }
        }
#endif

        SubObjects.Reset();
        GetObjectsWithOuter(BT, SubObjects);
        for (UObject* Obj : SubObjects)
        {
            if (Obj && Obj->IsA<UBehaviorTreeGraph>())
            {
                Graph = Cast<UEdGraph>(Obj);
                break;
            }
        }
    }

    if (Graph)
    {
        TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
        ResultObj->SetStringField(TEXT("graph_path"), Graph->GetPathName());
        ResultObj->SetStringField(TEXT("graph_name"), Graph->GetName());
        return ResultObj;
    }

    return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Behavior Tree has no graph"));
}

FJsonObjectParameter UMCPBehaviorTreeTools::HandleListBTGraphNodes(const FJsonObjectParameter& Params)
{
	// AI(GPT-5.2): C++ 侧读取 Graph->Nodes（Python 侧该属性常被标记为 protected 无法读取）
	FString GraphPath;
	if (!Params->TryGetStringField(TEXT("graph_path"), GraphPath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'graph_path' parameter"));
	}

	UEdGraph* Graph = LoadObject<UEdGraph>(nullptr, *GraphPath);
	if (!Graph)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Graph not found: %s"), *GraphPath));
	}

	TArray<TSharedPtr<FJsonValue>> NodesArray;
	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (!Node)
		{
			continue;
		}

		TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();
		NodeObj->SetStringField(TEXT("name"), Node->GetName());
		NodeObj->SetStringField(TEXT("path"), Node->GetPathName());
		NodeObj->SetStringField(TEXT("class"), Node->GetClass() ? Node->GetClass()->GetName() : TEXT(""));
		NodeObj->SetStringField(TEXT("guid"), Node->NodeGuid.ToString());
		NodeObj->SetNumberField(TEXT("pos_x"), Node->NodePosX);
		NodeObj->SetNumberField(TEXT("pos_y"), Node->NodePosY);

		// AI(GPT-5.2): 尽量通过反射提供“真实 BT 节点类型”信息（NodeInstance/ClassData），
		// 这样上层脚本不需要写死 Composite_Selector/Task_Wait 之类的具体节点类型。
		if (UBehaviorTreeGraphNode* BTGraphNode = Cast<UBehaviorTreeGraphNode>(Node))
		{
			UObject* NodeInstanceObj = BTGraphNode->NodeInstance;
			if (NodeInstanceObj)
			{
				NodeObj->SetStringField(TEXT("node_instance_path"), NodeInstanceObj->GetPathName());
				NodeObj->SetStringField(TEXT("node_instance_class"), NodeInstanceObj->GetClass() ? NodeInstanceObj->GetClass()->GetName() : TEXT(""));
				NodeObj->SetStringField(TEXT("node_instance_class_path"), NodeInstanceObj->GetClass() ? NodeInstanceObj->GetClass()->GetPathName() : TEXT(""));
			}
			else
			{
				NodeObj->SetStringField(TEXT("node_instance_path"), TEXT(""));
				NodeObj->SetStringField(TEXT("node_instance_class"), TEXT(""));
				NodeObj->SetStringField(TEXT("node_instance_class_path"), TEXT(""));
			}

			if (BTGraphNode->ClassData.GetClass())
			{
				NodeObj->SetStringField(TEXT("class_data_class"), BTGraphNode->ClassData.GetClass()->GetName());
				NodeObj->SetStringField(TEXT("class_data_class_path"), BTGraphNode->ClassData.GetClass()->GetPathName());
			}
			else
			{
				NodeObj->SetStringField(TEXT("class_data_class"), TEXT(""));
				NodeObj->SetStringField(TEXT("class_data_class_path"), TEXT(""));
			}
		}

		TArray<TSharedPtr<FJsonValue>> PinsArray;
		for (UEdGraphPin* Pin : Node->Pins)
		{
			if (!Pin)
			{
				continue;
			}
			TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
			PinObj->SetStringField(TEXT("name"), Pin->PinName.ToString());
			PinObj->SetStringField(TEXT("direction"), (Pin->Direction == EGPD_Input) ? TEXT("Input") : TEXT("Output"));
			PinObj->SetNumberField(TEXT("linked_to_count"), Pin->LinkedTo.Num());
			PinsArray.Add(MakeShared<FJsonValueObject>(PinObj));
		}
		NodeObj->SetArrayField(TEXT("pins"), PinsArray);

		NodesArray.Add(MakeShared<FJsonValueObject>(NodeObj));
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("graph_path"), Graph->GetPathName());
	ResultObj->SetStringField(TEXT("graph_name"), Graph->GetName());
	ResultObj->SetStringField(TEXT("graph_class"), Graph->GetClass() ? Graph->GetClass()->GetName() : TEXT(""));
	ResultObj->SetNumberField(TEXT("node_count"), Graph->Nodes.Num());
	ResultObj->SetArrayField(TEXT("nodes"), NodesArray);
	return FUnrealMCPCommonUtils::CreateSuccessResponse(ResultObj);
}

static UClass* _ResolveBTNodeClass(const FString& InClassStr)
{
	// AI(GPT-5.2): 支持 "/Script/AIModule.BTTask_Wait" 或 "BTTask_Wait"
	UClass* Cls = nullptr;
	if (InClassStr.IsEmpty())
	{
		return nullptr;
	}
	// 尝试 LoadClass（可处理 /Script 路径）
	Cls = LoadClass<UObject>(nullptr, *InClassStr);
	if (Cls)
	{
		return Cls;
	}
	// 尝试在已加载类中按名字查找
	Cls = FindFirstObject<UClass>(*InClassStr, EFindFirstObjectOptions::None);
	return Cls;
}

FJsonObjectParameter UMCPBehaviorTreeTools::HandleAddBTGraphNode(const FJsonObjectParameter& Params)
{
	// AI(GPT-5.2): 在 BT Graph 内创建 Task/Composite 节点（通过 ClassData + PostPlacedNewNode 生成 NodeInstance）
	FString GraphPath;
	if (!Params->TryGetStringField(TEXT("graph_path"), GraphPath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'graph_path' parameter"));
	}

	FString BTNodeClassStr;
	if (!Params->TryGetStringField(TEXT("bt_node_class"), BTNodeClassStr))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'bt_node_class' parameter"));
	}

	int32 PosX = 0;
	int32 PosY = 0;
	{
		// TryGetNumberField 返回 double，这里做显式转换
		double DX = 0.0;
		double DY = 0.0;
		if (Params->TryGetNumberField(TEXT("pos_x"), DX))
		{
			PosX = static_cast<int32>(DX);
		}
		if (Params->TryGetNumberField(TEXT("pos_y"), DY))
		{
			PosY = static_cast<int32>(DY);
		}
	}

	UBehaviorTreeGraph* Graph = Cast<UBehaviorTreeGraph>(LoadObject<UEdGraph>(nullptr, *GraphPath));
	if (!Graph)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("BehaviorTreeGraph not found: %s"), *GraphPath));
	}

	UClass* BTNodeClass = _ResolveBTNodeClass(BTNodeClassStr);
	if (!BTNodeClass)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("BT node class not found: %s"), *BTNodeClassStr));
	}

	UBehaviorTreeGraphNode* NewNode = nullptr;
	if (BTNodeClass->IsChildOf(UBTTaskNode::StaticClass()))
	{
		NewNode = NewObject<UBehaviorTreeGraphNode_Task>(Graph);
	}
	else if (BTNodeClass->IsChildOf(UBTCompositeNode::StaticClass()))
	{
		NewNode = NewObject<UBehaviorTreeGraphNode_Composite>(Graph);
	}
	else
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Unsupported bt_node_class: only BTTaskNode/BTCompositeNode are supported currently"));
	}

	if (!NewNode)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create graph node"));
	}

	Graph->Modify();
	NewNode->SetFlags(RF_Transactional);
	NewNode->CreateNewGuid();
	NewNode->NodePosX = PosX;
	NewNode->NodePosY = PosY;

	// 设置运行时实例类（PostPlacedNewNode 会用它来 NewObject NodeInstance）
	NewNode->ClassData = FGraphNodeClassData(BTNodeClass, FString());

	Graph->AddNode(NewNode, true, false);
	NewNode->PostPlacedNewNode();
	NewNode->AllocateDefaultPins();
	NewNode->InitializeInstance();
	NewNode->UpdateErrorMessage();

	Graph->UpdateAsset();

	TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();
	NodeObj->SetStringField(TEXT("path"), NewNode->GetPathName());
	NodeObj->SetStringField(TEXT("name"), NewNode->GetName());
	NodeObj->SetStringField(TEXT("class"), NewNode->GetClass() ? NewNode->GetClass()->GetName() : TEXT(""));
	NodeObj->SetStringField(TEXT("guid"), NewNode->NodeGuid.ToString());

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("graph_path"), Graph->GetPathName());
	ResultObj->SetObjectField(TEXT("node"), NodeObj);
	return FUnrealMCPCommonUtils::CreateSuccessResponse(ResultObj);
}

FJsonObjectParameter UMCPBehaviorTreeTools::HandleConnectBTGraphNodes(const FJsonObjectParameter& Params)
{
	// AI(GPT-5.2): 父->子连线（使用 Schema.TryCreateConnection）
	FString GraphPath;
	if (!Params->TryGetStringField(TEXT("graph_path"), GraphPath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'graph_path' parameter"));
	}

	FString ParentNodePath;
	if (!Params->TryGetStringField(TEXT("parent_node_path"), ParentNodePath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'parent_node_path' parameter"));
	}

	FString ChildNodePath;
	if (!Params->TryGetStringField(TEXT("child_node_path"), ChildNodePath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'child_node_path' parameter"));
	}

	UBehaviorTreeGraph* Graph = Cast<UBehaviorTreeGraph>(LoadObject<UEdGraph>(nullptr, *GraphPath));
	if (!Graph)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("BehaviorTreeGraph not found: %s"), *GraphPath));
	}

	UAIGraphNode* ParentNode = LoadObject<UAIGraphNode>(nullptr, *ParentNodePath);
	UAIGraphNode* ChildNode = LoadObject<UAIGraphNode>(nullptr, *ChildNodePath);
	if (!ParentNode || !ChildNode)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Parent/Child node not found"));
	}

	UEdGraphPin* OutPin = ParentNode->GetOutputPin(0);
	UEdGraphPin* InPin = ChildNode->GetInputPin(0);
	if (!OutPin || !InPin)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to resolve default pins (output/input)"));
	}

	const UEdGraphSchema* Schema = Graph->GetSchema();
	bool bOk = false;
	FString Err;
	if (Schema)
	{
		bOk = Schema->TryCreateConnection(OutPin, InPin);
	}
	else
	{
		// fallback
		OutPin->MakeLinkTo(InPin);
		bOk = true;
	}

	Graph->UpdateAsset();

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetBoolField(TEXT("connected"), bOk);
	ResultObj->SetStringField(TEXT("parent"), ParentNode->GetPathName());
	ResultObj->SetStringField(TEXT("child"), ChildNode->GetPathName());
	return bOk ? FUnrealMCPCommonUtils::CreateSuccessResponse(ResultObj)
	           : FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("TryCreateConnection failed"));
}

FJsonObjectParameter UMCPBehaviorTreeTools::HandleCreateBehaviorTree(const FJsonObjectParameter& Params)
{
    FString Name;
    if (!Params->TryGetStringField(TEXT("name"), Name))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    FString PackagePath = TEXT("/Game/");
    Params->TryGetStringField(TEXT("package_path"), PackagePath);

    FString AssetName = Name;
    FString FinalPath = FPaths::Combine(PackagePath, AssetName);
    
    if (UEditorAssetLibrary::DoesAssetExist(FinalPath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Asset already exists: %s"), *FinalPath));
    }

    UBehaviorTreeFactory* Factory = NewObject<UBehaviorTreeFactory>();
    UPackage* Package = CreatePackage(*FinalPath);
    UBehaviorTree* NewBT = Cast<UBehaviorTree>(Factory->FactoryCreateNew(UBehaviorTree::StaticClass(), Package, *AssetName, RF_Standalone | RF_Public, nullptr, GWarn));

    if (NewBT)
    {
        FAssetRegistryModule::AssetCreated(NewBT);
        Package->MarkPackageDirty();

        TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
        ResultObj->SetStringField(TEXT("name"), AssetName);
        ResultObj->SetStringField(TEXT("path"), NewBT->GetPathName());
        return ResultObj;
    }

    return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create Behavior Tree"));
}

FJsonObjectParameter UMCPBehaviorTreeTools::HandleGetBTAuxiliaryNodes(const FJsonObjectParameter& Params)
{
    // AI(GPT-5.2): 兼容扩展
    // Live Coding 在运行时新增 UFUNCTION 往往需要重启编辑器才能反射到 Python。
    // 为了在不重启的前提下提供“创建行为树”所需的能力，这里复用已存在的 UFUNCTION 作为多路复用入口：
    // - op == "list_nodes"  -> 使用 graph_path 列出 BT Graph 节点
    // - op == "add_node"    -> 使用 graph_path + bt_node_class (+ pos_x/pos_y) 创建节点
    // - op == "connect"     -> 使用 graph_path + parent_node_path + child_node_path 连接
    // - op == "set_wait_time" -> 使用 node_path + wait_time 设置 BTTask_Wait.WaitTime
    FString Op;
    if (Params->TryGetStringField(TEXT("op"), Op))
    {
        if (Op.Equals(TEXT("list_nodes"), ESearchCase::IgnoreCase))
        {
            return HandleListBTGraphNodes(Params);
        }
        if (Op.Equals(TEXT("add_node"), ESearchCase::IgnoreCase))
        {
            return HandleAddBTGraphNode(Params);
        }
        if (Op.Equals(TEXT("connect"), ESearchCase::IgnoreCase))
        {
            return HandleConnectBTGraphNodes(Params);
        }
        if (Op.Equals(TEXT("set_wait_time"), ESearchCase::IgnoreCase))
        {
            FString NodePath;
            if (!Params->TryGetStringField(TEXT("node_path"), NodePath))
            {
                return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'node_path' parameter"));
            }
            double WaitTime = 0.0;
            if (!Params->TryGetNumberField(TEXT("wait_time"), WaitTime))
            {
                return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'wait_time' parameter"));
            }

            UBehaviorTreeGraphNode_Task* TaskGraphNode = LoadObject<UBehaviorTreeGraphNode_Task>(nullptr, *NodePath);
            if (!TaskGraphNode)
            {
                return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Node not found or not a BT Task Graph Node"));
            }

            // NodeInstance 来自 UAIGraphNode（C++ 可访问，Python 侧常被标记为 protected）
            UBTTask_Wait* WaitTask = Cast<UBTTask_Wait>(TaskGraphNode->NodeInstance);
            if (!WaitTask)
            {
                return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("NodeInstance is not BTTask_Wait (or not initialized)"));
            }

            TaskGraphNode->Modify();
            WaitTask->Modify();
            WaitTask->WaitTime = static_cast<float>(WaitTime);

            if (UBehaviorTreeGraph* Graph = Cast<UBehaviorTreeGraph>(TaskGraphNode->GetGraph()))
            {
                Graph->UpdateAsset();
            }
            WaitTask->MarkPackageDirty();

            TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
            ResultObj->SetStringField(TEXT("node_path"), TaskGraphNode->GetPathName());
            // AI(GPT-5.2): UE5.7 中 WaitTime 是 FValueOrBBKey_Float，GetValue 需要 BehaviorComp/Blackboard 参数；
            // 这里返回刚刚设置的默认值（避免依赖运行时 BehaviorTreeComponent）。
            ResultObj->SetNumberField(TEXT("wait_time"), static_cast<float>(WaitTime));
            return FUnrealMCPCommonUtils::CreateSuccessResponse(ResultObj);
        }
		if (Op.Equals(TEXT("add_service"), ESearchCase::IgnoreCase))
		{
			// AI(GPT-5.2): 为 BehaviorTreeGraphNode 添加一个 Service（解决 Python 侧 Services 属性受保护无法读写的问题）。
			FString ParentNodePath;
			if (!Params->TryGetStringField(TEXT("parent_node_path"), ParentNodePath))
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'parent_node_path' parameter"));
			}
			FString ServiceClassStr;
			if (!Params->TryGetStringField(TEXT("service_class"), ServiceClassStr))
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'service_class' parameter"));
			}

			int32 PosX = 0;
			int32 PosY = 0;
			{
				double DX = 0.0;
				double DY = 0.0;
				if (Params->TryGetNumberField(TEXT("pos_x"), DX))
				{
					PosX = static_cast<int32>(DX);
				}
				if (Params->TryGetNumberField(TEXT("pos_y"), DY))
				{
					PosY = static_cast<int32>(DY);
				}
			}

			UBehaviorTreeGraphNode* ParentNode = LoadObject<UBehaviorTreeGraphNode>(nullptr, *ParentNodePath);
			if (!ParentNode)
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Parent node not found: %s"), *ParentNodePath));
			}

			UBehaviorTreeGraph* Graph = Cast<UBehaviorTreeGraph>(ParentNode->GetGraph());
			if (!Graph)
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Parent node has no BehaviorTreeGraph"));
			}

			UClass* ServiceClass = _ResolveBTNodeClass(ServiceClassStr);
			if (!ServiceClass)
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Service class not found: %s"), *ServiceClassStr));
			}
			if (!ServiceClass->IsChildOf(UBTService::StaticClass()))
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("service_class must be a UBTService subclass"));
			}

			Graph->Modify();
			ParentNode->Modify();

			UBehaviorTreeGraphNode_Service* NewServiceNode = NewObject<UBehaviorTreeGraphNode_Service>(Graph);
			if (!NewServiceNode)
			{
				return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create BehaviorTreeGraphNode_Service"));
			}

			NewServiceNode->SetFlags(RF_Transactional);
			NewServiceNode->CreateNewGuid();
			// AI(GPT-5.2): 服务节点默认贴近父节点，方便在编辑器里观察（即使 UI 不展示该节点也不影响运行）。
			NewServiceNode->NodePosX = (PosX != 0) ? PosX : (ParentNode->NodePosX + 120);
			NewServiceNode->NodePosY = (PosY != 0) ? PosY : (ParentNode->NodePosY + 80);

			NewServiceNode->ClassData = FGraphNodeClassData(ServiceClass, FString());
			Graph->AddNode(NewServiceNode, true, false);
			NewServiceNode->PostPlacedNewNode();
			NewServiceNode->AllocateDefaultPins();
			NewServiceNode->InitializeInstance();
			NewServiceNode->UpdateErrorMessage();

			// AI(GPT-5.2): 挂到父节点的 Services 数组（C++ 可访问，Python 侧受保护）。
			ParentNode->Services.Add(NewServiceNode);

			Graph->UpdateAsset();
			NewServiceNode->MarkPackageDirty();

			TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();
			NodeObj->SetStringField(TEXT("parent_node_path"), ParentNode->GetPathName());
			NodeObj->SetStringField(TEXT("service_node_path"), NewServiceNode->GetPathName());
			NodeObj->SetStringField(TEXT("service_node_guid"), NewServiceNode->NodeGuid.ToString());
			if (NewServiceNode->NodeInstance)
			{
				NodeObj->SetStringField(TEXT("service_instance_path"), NewServiceNode->NodeInstance->GetPathName());
				NodeObj->SetStringField(TEXT("service_instance_class"), NewServiceNode->NodeInstance->GetClass() ? NewServiceNode->NodeInstance->GetClass()->GetName() : TEXT(""));
				NodeObj->SetStringField(TEXT("service_instance_class_path"), NewServiceNode->NodeInstance->GetClass() ? NewServiceNode->NodeInstance->GetClass()->GetPathName() : TEXT(""));
			}
			return FUnrealMCPCommonUtils::CreateSuccessResponse(NodeObj);
		}
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown op: %s"), *Op));
    }

    FString NodePath;
    if (!Params->TryGetStringField(TEXT("node_path"), NodePath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'node_path' parameter"));
    }

    UBehaviorTreeGraphNode* GraphNode = LoadObject<UBehaviorTreeGraphNode>(nullptr, *NodePath);
    if (!GraphNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Node not found or not a BT Graph Node"));
    }

    TArray<TSharedPtr<FJsonValue>> AuxNodesArray;
	// AI(GPT-5.2): 通过反射补充 Decorator/Service 的 NodeInstance 类型信息，便于上层判断是否存在“射击/瞄准”等逻辑节点。
	auto AppendAuxNode = [&AuxNodesArray](UObject* Obj)
	{
		if (!Obj)
		{
			return;
		}
		TSharedPtr<FJsonObject> AuxObj = MakeShared<FJsonObject>();
		AuxObj->SetStringField(TEXT("name"), Obj->GetName());
		AuxObj->SetStringField(TEXT("class"), Obj->GetClass() ? Obj->GetClass()->GetName() : TEXT(""));
		AuxObj->SetStringField(TEXT("path"), Obj->GetPathName());

		if (UBehaviorTreeGraphNode* AuxGraphNode = Cast<UBehaviorTreeGraphNode>(Obj))
		{
			UObject* NodeInstanceObj = AuxGraphNode->NodeInstance;
			if (NodeInstanceObj)
			{
				AuxObj->SetStringField(TEXT("node_instance_path"), NodeInstanceObj->GetPathName());
				AuxObj->SetStringField(TEXT("node_instance_class"), NodeInstanceObj->GetClass() ? NodeInstanceObj->GetClass()->GetName() : TEXT(""));
				AuxObj->SetStringField(TEXT("node_instance_class_path"), NodeInstanceObj->GetClass() ? NodeInstanceObj->GetClass()->GetPathName() : TEXT(""));
			}
			else
			{
				AuxObj->SetStringField(TEXT("node_instance_path"), TEXT(""));
				AuxObj->SetStringField(TEXT("node_instance_class"), TEXT(""));
				AuxObj->SetStringField(TEXT("node_instance_class_path"), TEXT(""));
			}
		}
		AuxNodesArray.Add(MakeShared<FJsonValueObject>(AuxObj));
	};

    for (auto& ObjPtr : GraphNode->Decorators)
    {
		AppendAuxNode(ObjPtr);
    }
    
    for (auto& ObjPtr : GraphNode->Services)
    {
		AppendAuxNode(ObjPtr);
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("auxiliary_nodes"), AuxNodesArray);
    return ResultObj;
}
