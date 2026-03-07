// Fill out your copyright notice in the Description page of Project Settings.

#include "MCPTools/MCPSlateTools.h"
#include "MCPTools/UnrealMCPCommonUtils.h"

#include "Framework/Application/SlateApplication.h"
#include "Framework/Docking/TabManager.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Layout/WidgetPath.h"
#include "Widgets/SWindow.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SEditableText.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h"
#include "Input/Events.h"
#include "InputCoreTypes.h"

// ─────────────────────────────────────────────────────────────────────────────
// 内部辅助工具
// ─────────────────────────────────────────────────────────────────────────────

/** 把 EWindowType 枚举转为可读字符串 */
static FString WindowTypeToString(EWindowType Type)
{
	switch (Type)
	{
	case EWindowType::Normal:          return TEXT("Normal");
	case EWindowType::Menu:            return TEXT("Menu");
	case EWindowType::ToolTip:         return TEXT("ToolTip");
	case EWindowType::Notification:    return TEXT("Notification");
	case EWindowType::CursorDecorator: return TEXT("CursorDecorator");
	case EWindowType::GameWindow:      return TEXT("GameWindow");
	default:                           return TEXT("Unknown");
	}
}

/** 把 EVisibility 枚举转为可读字符串 */
static FString VisibilityToString(EVisibility V)
{
	if (V == EVisibility::Visible)   return TEXT("Visible");
	if (V == EVisibility::Hidden)    return TEXT("Hidden");
	if (V == EVisibility::Collapsed) return TEXT("Collapsed");
	return TEXT("SelfHitTestInvisible");
}

// ─────────────────────────────────────────────────────────────────────────────
// Private helpers
// ─────────────────────────────────────────────────────────────────────────────

TSharedPtr<FJsonObject> UMCPSlateTools::WidgetToJson(TSharedRef<SWidget> Widget, int32 MaxDepth, int32 CurrentDepth)
{
	TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
	Obj->SetStringField(TEXT("type"),       Widget->GetType().ToString());
	Obj->SetStringField(TEXT("tag"),        Widget->GetTag().ToString());
	Obj->SetStringField(TEXT("visibility"), VisibilityToString(Widget->GetVisibility()));

	// 针对常用文本类控件提取文本内容
	const FName WidgetType = Widget->GetType();
	if (WidgetType == "STextBlock")
	{
		TSharedRef<STextBlock> TB = StaticCastSharedRef<STextBlock>(Widget);
		Obj->SetStringField(TEXT("text"), TB->GetText().ToString());
	}
	else if (WidgetType == "SEditableText")
	{
		TSharedRef<SEditableText> ET = StaticCastSharedRef<SEditableText>(Widget);
		Obj->SetStringField(TEXT("text"),      ET->GetText().ToString());
		Obj->SetStringField(TEXT("hint_text"), ET->GetHintText().ToString());
	}
	else if (WidgetType == "SEditableTextBox")
	{
		TSharedRef<SEditableTextBox> ETB = StaticCastSharedRef<SEditableTextBox>(Widget);
		Obj->SetStringField(TEXT("text"), ETB->GetText().ToString());
	}
	else if (WidgetType == "SMultiLineEditableTextBox")
	{
		TSharedRef<SMultiLineEditableTextBox> MLETB = StaticCastSharedRef<SMultiLineEditableTextBox>(Widget);
		Obj->SetStringField(TEXT("hint_text"), MLETB->GetHintText().ToString());
	}

	// 递归子节点（受 MaxDepth 限制）
	if (CurrentDepth < MaxDepth)
	{
		FChildren* Children = Widget->GetChildren();
		if (Children && Children->Num() > 0)
		{
			TArray<TSharedPtr<FJsonValue>> ChildArray;
			const int32 ChildCount = FMath::Min(Children->Num(), 64); // 单层最多 64 个，防止爆炸
			for (int32 i = 0; i < ChildCount; i++)
			{
				TSharedRef<SWidget> Child = Children->GetChildAt(i);
				TSharedPtr<FJsonObject> ChildObj = WidgetToJson(Child, MaxDepth, CurrentDepth + 1);
				ChildArray.Add(MakeShared<FJsonValueObject>(ChildObj));
			}
			if (Children->Num() > 64)
			{
				TSharedPtr<FJsonObject> TruncObj = MakeShared<FJsonObject>();
				TruncObj->SetStringField(TEXT("type"), FString::Printf(TEXT("... (%d more children truncated)"), Children->Num() - 64));
				ChildArray.Add(MakeShared<FJsonValueObject>(TruncObj));
			}
			Obj->SetArrayField(TEXT("children"), ChildArray);
		}
	}
	else
	{
		// 达到深度限制时仅记录子节点数量
		FChildren* Children = Widget->GetChildren();
		if (Children && Children->Num() > 0)
		{
			Obj->SetNumberField(TEXT("children_count_truncated"), Children->Num());
		}
	}

	return Obj;
}

void UMCPSlateTools::FindWidgetsByTypeRecursive(
	TSharedPtr<SWidget> Widget,
	const FName& TypeName,
	const FString& WindowTitle,
	TArray<TSharedPtr<FJsonValue>>& OutArray,
	int32 MaxDepth,
	int32 CurrentDepth)
{
	if (!Widget.IsValid() || CurrentDepth > MaxDepth) return;

	if (Widget->GetType() == TypeName)
	{
		TSharedPtr<FJsonObject> WidgetObj = MakeShared<FJsonObject>();
		WidgetObj->SetStringField(TEXT("type"),        Widget->GetType().ToString());
		WidgetObj->SetStringField(TEXT("tag"),         Widget->GetTag().ToString());
		WidgetObj->SetStringField(TEXT("visibility"),  VisibilityToString(Widget->GetVisibility()));
		WidgetObj->SetStringField(TEXT("in_window"),   WindowTitle);
		WidgetObj->SetNumberField(TEXT("depth"),       CurrentDepth);

		const FName WT = Widget->GetType();
		if (WT == "STextBlock")
		{
			TSharedRef<STextBlock> TB = StaticCastSharedRef<STextBlock>(Widget.ToSharedRef());
			WidgetObj->SetStringField(TEXT("text"), TB->GetText().ToString());
		}
		else if (WT == "SEditableText")
		{
			TSharedRef<SEditableText> ET = StaticCastSharedRef<SEditableText>(Widget.ToSharedRef());
			WidgetObj->SetStringField(TEXT("text"),      ET->GetText().ToString());
			WidgetObj->SetStringField(TEXT("hint_text"), ET->GetHintText().ToString());
		}
		else if (WT == "SEditableTextBox")
		{
			TSharedRef<SEditableTextBox> ETB = StaticCastSharedRef<SEditableTextBox>(Widget.ToSharedRef());
			WidgetObj->SetStringField(TEXT("text"), ETB->GetText().ToString());
		}

		OutArray.Add(MakeShared<FJsonValueObject>(WidgetObj));
	}

	FChildren* Children = Widget->GetChildren();
	if (Children)
	{
		for (int32 i = 0; i < Children->Num(); i++)
		{
			FindWidgetsByTypeRecursive(
				Children->GetChildAt(i).ToSharedPtr(),
				TypeName, WindowTitle, OutArray,
				MaxDepth, CurrentDepth + 1);
		}
	}
}

TArray<TSharedPtr<FJsonValue>> UMCPSlateTools::WidgetPathToJsonArray(const FWidgetPath& WidgetPath)
{
	TArray<TSharedPtr<FJsonValue>> PathArray;
	for (int32 i = 0; i < WidgetPath.Widgets.Num(); i++)
	{
		const TSharedRef<SWidget>& W = WidgetPath.Widgets[i].Widget;
		TSharedPtr<FJsonObject> WObj = MakeShared<FJsonObject>();
		WObj->SetStringField(TEXT("type"), W->GetType().ToString());
		WObj->SetStringField(TEXT("tag"),  W->GetTag().ToString());

		if (W->GetType() == "STextBlock")
		{
			TSharedRef<STextBlock> TB = StaticCastSharedRef<STextBlock>(W);
			WObj->SetStringField(TEXT("text"), TB->GetText().ToString());
		}

		// 几何信息（绝对坐标与大小）
		const FGeometry& Geo = WidgetPath.Widgets[i].Geometry;
		const FVector2D AbsPos  = Geo.GetAbsolutePosition();
		const FVector2D AbsSize = Geo.GetAbsoluteSize();
		TSharedPtr<FJsonObject> GeoObj = MakeShared<FJsonObject>();
		GeoObj->SetNumberField(TEXT("x"),      AbsPos.X);
		GeoObj->SetNumberField(TEXT("y"),      AbsPos.Y);
		GeoObj->SetNumberField(TEXT("width"),  AbsSize.X);
		GeoObj->SetNumberField(TEXT("height"), AbsSize.Y);
		WObj->SetObjectField(TEXT("geometry"), GeoObj);

		PathArray.Add(MakeShared<FJsonValueObject>(WObj));
	}
	return PathArray;
}

// ─────────────────────────────────────────────────────────────────────────────
// Public tool implementations
// ─────────────────────────────────────────────────────────────────────────────

FJsonObjectParameter UMCPSlateTools::HandleGetAllWindows(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	const TArray<TSharedRef<SWindow>>& TopWindows = FSlateApplication::Get().GetTopLevelWindows();

	TArray<TSharedPtr<FJsonValue>> WindowsArray;
	for (int32 i = 0; i < TopWindows.Num(); i++)
	{
		const TSharedRef<SWindow>& Win = TopWindows[i];
		TSharedPtr<FJsonObject> WinObj = MakeShared<FJsonObject>();

		WinObj->SetNumberField(TEXT("index"),      i);
		WinObj->SetStringField(TEXT("title"),      Win->GetTitle().ToString());
		WinObj->SetStringField(TEXT("window_type"),WindowTypeToString(Win->GetType()));
		WinObj->SetStringField(TEXT("widget_type"),Win->GetTypeAsString());
		WinObj->SetBoolField  (TEXT("is_visible"), Win->IsVisible());
		WinObj->SetBoolField  (TEXT("is_active"),  Win->IsActive());
		WinObj->SetBoolField  (TEXT("is_focused"),
			FSlateApplication::Get().GetActiveTopLevelWindow() == Win);

		const FVector2D Pos  = Win->GetPositionInScreen();
		const FVector2D Size = Win->GetSizeInScreen();

		TSharedPtr<FJsonObject> PosObj = MakeShared<FJsonObject>();
		PosObj->SetNumberField(TEXT("x"), Pos.X);
		PosObj->SetNumberField(TEXT("y"), Pos.Y);
		WinObj->SetObjectField(TEXT("position"), PosObj);

		TSharedPtr<FJsonObject> SizeObj = MakeShared<FJsonObject>();
		SizeObj->SetNumberField(TEXT("width"),  Size.X);
		SizeObj->SetNumberField(TEXT("height"), Size.Y);
		WinObj->SetObjectField(TEXT("size"), SizeObj);

		FChildren* Children = Win->GetChildren();
		WinObj->SetNumberField(TEXT("direct_child_count"), Children ? Children->Num() : 0);

		WindowsArray.Add(MakeShared<FJsonValueObject>(WinObj));
	}

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("windows"), WindowsArray);
	Result->SetNumberField(TEXT("count"),  WindowsArray.Num());
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleGetWidgetTree(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	// 解析参数
	double WindowIndexD = -1.0;
	int32  WindowIndex  = -1;
	FString WindowTitle;
	Params->TryGetNumberField(TEXT("window_index"), WindowIndexD);
	WindowIndex = (int32)WindowIndexD;
	Params->TryGetStringField(TEXT("window_title"), WindowTitle);

	double MaxDepthD = 5.0;
	Params->TryGetNumberField(TEXT("max_depth"), MaxDepthD);
	const int32 MaxDepth = FMath::Clamp((int32)MaxDepthD, 1, 12);

	// 定位目标窗口
	const TArray<TSharedRef<SWindow>>& TopWindows = FSlateApplication::Get().GetTopLevelWindows();
	TSharedPtr<SWindow> TargetWindow;

	if (WindowIndex >= 0 && WindowIndex < TopWindows.Num())
	{
		TargetWindow = TopWindows[WindowIndex].ToSharedPtr();
	}
	else if (!WindowTitle.IsEmpty())
	{
		for (const TSharedRef<SWindow>& Win : TopWindows)
		{
			if (Win->GetTitle().ToString().Contains(WindowTitle))
			{
				TargetWindow = Win.ToSharedPtr();
				break;
			}
		}
	}
	else
	{
		// 默认取第一个可见激活窗口，否则取第一个
		for (const TSharedRef<SWindow>& Win : TopWindows)
		{
			if (Win->IsVisible())
			{
				TargetWindow = Win.ToSharedPtr();
				if (Win->IsActive()) break;
			}
		}
	}

	if (!TargetWindow.IsValid())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No matching window found"));
	}

	TSharedPtr<FJsonObject> Tree = WidgetToJson(TargetWindow.ToSharedRef(), MaxDepth, 0);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("window_title"), TargetWindow->GetTitle().ToString());
	Result->SetNumberField(TEXT("max_depth"),     MaxDepth);
	Result->SetObjectField(TEXT("widget_tree"),   Tree);
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleGetWidgetUnderCursor(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	const FVector2f CursorPos = FSlateApplication::Get().GetCursorPos();
	const TArray<TSharedRef<SWindow>>& Windows = FSlateApplication::Get().GetTopLevelWindows();
	FWidgetPath WidgetPath = FSlateApplication::Get().LocateWindowUnderMouse(CursorPos, Windows, true);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("cursor_x"), CursorPos.X);
	Result->SetNumberField(TEXT("cursor_y"), CursorPos.Y);

	if (!WidgetPath.IsValid())
	{
		Result->SetBoolField(TEXT("found"), false);
		return Result;
	}

	Result->SetBoolField(TEXT("found"), true);
	Result->SetStringField(TEXT("window_title"), WidgetPath.GetWindow()->GetTitle().ToString());

	TArray<TSharedPtr<FJsonValue>> PathArray = WidgetPathToJsonArray(WidgetPath);
	Result->SetArrayField(TEXT("widget_path"), PathArray);

	// 最顶层叶子 Widget
	TSharedRef<SWidget> LeafWidget = WidgetPath.GetLastWidget();
	Result->SetStringField(TEXT("leaf_widget_type"), LeafWidget->GetType().ToString());
	Result->SetStringField(TEXT("leaf_widget_tag"),  LeafWidget->GetTag().ToString());

	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleGetWidgetAtPosition(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	double X = 0.0, Y = 0.0;
	if (!Params->TryGetNumberField(TEXT("x"), X) || !Params->TryGetNumberField(TEXT("y"), Y))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'x' or 'y' parameter"));
	}

	const FVector2f QueryPos(X, Y);
	const TArray<TSharedRef<SWindow>>& Windows = FSlateApplication::Get().GetTopLevelWindows();
	FWidgetPath WidgetPath = FSlateApplication::Get().LocateWindowUnderMouse(QueryPos, Windows, true);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("query_x"), X);
	Result->SetNumberField(TEXT("query_y"), Y);

	if (!WidgetPath.IsValid())
	{
		Result->SetBoolField(TEXT("found"), false);
		return Result;
	}

	Result->SetBoolField(TEXT("found"), true);
	Result->SetStringField(TEXT("window_title"), WidgetPath.GetWindow()->GetTitle().ToString());

	TArray<TSharedPtr<FJsonValue>> PathArray = WidgetPathToJsonArray(WidgetPath);
	Result->SetArrayField(TEXT("widget_path"), PathArray);

	TSharedRef<SWidget> LeafWidget = WidgetPath.GetLastWidget();
	Result->SetStringField(TEXT("leaf_widget_type"), LeafWidget->GetType().ToString());

	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleFindWidgetsByType(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	FString TypeName;
	if (!Params->TryGetStringField(TEXT("type_name"), TypeName) || TypeName.IsEmpty())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'type_name' parameter"));
	}

	double WindowIndexD = -1.0;
	int32  WindowIndex  = -1;
	FString WindowTitle;
	Params->TryGetNumberField(TEXT("window_index"), WindowIndexD);
	WindowIndex = (int32)WindowIndexD;
	Params->TryGetStringField(TEXT("window_title"), WindowTitle);

	double MaxDepthD = 8.0;
	Params->TryGetNumberField(TEXT("max_depth"), MaxDepthD);
	const int32 MaxDepth = FMath::Clamp((int32)MaxDepthD, 1, 15);

	const TArray<TSharedRef<SWindow>>& TopWindows = FSlateApplication::Get().GetTopLevelWindows();

	// 确定搜索范围
	TArray<TSharedPtr<SWindow>> SearchWindows;
	if (WindowIndex >= 0 && WindowIndex < TopWindows.Num())
	{
		SearchWindows.Add(TopWindows[WindowIndex].ToSharedPtr());
	}
	else if (!WindowTitle.IsEmpty())
	{
		for (const TSharedRef<SWindow>& Win : TopWindows)
		{
			if (Win->GetTitle().ToString().Contains(WindowTitle))
			{
				SearchWindows.Add(Win.ToSharedPtr());
				break;
			}
		}
	}
	else
	{
		for (const TSharedRef<SWindow>& Win : TopWindows)
		{
			SearchWindows.Add(Win.ToSharedPtr());
		}
	}

	TArray<TSharedPtr<FJsonValue>> FoundWidgets;
	for (const TSharedPtr<SWindow>& Win : SearchWindows)
	{
		FindWidgetsByTypeRecursive(
			Win, FName(*TypeName),
			Win->GetTitle().ToString(),
			FoundWidgets, MaxDepth, 0);
	}

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("widgets"), FoundWidgets);
	Result->SetNumberField(TEXT("count"),  FoundWidgets.Num());
	Result->SetStringField(TEXT("searched_type"), TypeName);
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleClickAtPosition(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	double X = 0.0, Y = 0.0;
	if (!Params->TryGetNumberField(TEXT("x"), X) || !Params->TryGetNumberField(TEXT("y"), Y))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'x' or 'y' parameter"));
	}

	FString ButtonStr = TEXT("Left");
	Params->TryGetStringField(TEXT("button"), ButtonStr);

	FKey MouseKey = EKeys::LeftMouseButton;
	if (ButtonStr == TEXT("Right"))       MouseKey = EKeys::RightMouseButton;
	else if (ButtonStr == TEXT("Middle")) MouseKey = EKeys::MiddleMouseButton;

	const FVector2f ClickPos(static_cast<float>(X), static_cast<float>(Y));
	const TArray<TSharedRef<SWindow>>& Windows = FSlateApplication::Get().GetTopLevelWindows();
	FWidgetPath WidgetPath = FSlateApplication::Get().LocateWindowUnderMouse(ClickPos, Windows, true);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	if (!WidgetPath.IsValid())
	{
		Result->SetBoolField(TEXT("success"), false);
		Result->SetStringField(TEXT("error"), TEXT("No widget found at the given position"));
		return Result;
	}

	// 鼠标按下
	FPointerEvent MouseDownEvent(
		0,
		ClickPos, ClickPos,
		TSet<FKey>({ MouseKey }),
		MouseKey,
		0.0f,
		FModifierKeysState());
	FSlateApplication::Get().RoutePointerDownEvent(WidgetPath, MouseDownEvent);

	// 鼠标抬起（重新定位一次防止路径过期）
	FWidgetPath WidgetPathUp = FSlateApplication::Get().LocateWindowUnderMouse(ClickPos, Windows, true);
	FPointerEvent MouseUpEvent(
		0,
		ClickPos, ClickPos,
		TSet<FKey>(),
		MouseKey,
		0.0f,
		FModifierKeysState());

	if (WidgetPathUp.IsValid())
	{
		FSlateApplication::Get().RoutePointerUpEvent(WidgetPathUp, MouseUpEvent);
	}

	Result->SetBoolField(TEXT("success"),             true);
	Result->SetNumberField(TEXT("x"),                 X);
	Result->SetNumberField(TEXT("y"),                 Y);
	Result->SetStringField(TEXT("button"),            ButtonStr);
	Result->SetStringField(TEXT("clicked_widget_type"),
		WidgetPath.GetLastWidget()->GetType().ToString());
	Result->SetStringField(TEXT("clicked_widget_tag"),
		WidgetPath.GetLastWidget()->GetTag().ToString());
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleSendTextInput(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	FString Text;
	if (!Params->TryGetStringField(TEXT("text"), Text))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'text' parameter"));
	}

	const FModifierKeysState NoModifiers;
	int32 SentCount = 0;
	for (const TCHAR Ch : Text)
	{
		FCharacterEvent CharEvent(Ch, NoModifiers, 0, false);
		FSlateApplication::Get().ProcessKeyCharEvent(CharEvent);
		SentCount++;
	}

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"),    true);
	Result->SetStringField(TEXT("text"),       Text);
	Result->SetNumberField(TEXT("char_count"), SentCount);
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleSendKeyPress(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));
	}

	FString KeyStr;
	if (!Params->TryGetStringField(TEXT("key"), KeyStr) || KeyStr.IsEmpty())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'key' parameter"));
	}

	bool bShift = false, bCtrl = false, bAlt = false;
	Params->TryGetBoolField(TEXT("shift"), bShift);
	Params->TryGetBoolField(TEXT("ctrl"),  bCtrl);
	Params->TryGetBoolField(TEXT("alt"),   bAlt);

	// 文本输入（可选，发送 char 事件附带在同一次按键中）
	FString AdditionalText;
	Params->TryGetStringField(TEXT("text"), AdditionalText);

	const FModifierKeysState Modifiers(bShift, bShift, bCtrl, bCtrl, bAlt, bAlt, false, false, false);
	const FKey Key(*KeyStr);

	if (!Key.IsValid())
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Invalid key name: '%s'. Use standard UE key names like Enter, Escape, Tab, BackSpace, Delete, A, B, ..."), *KeyStr));
	}

	FKeyEvent KeyDownEvent(Key, Modifiers, 0, false, 0, 0);
	const bool bHandled = FSlateApplication::Get().ProcessKeyDownEvent(KeyDownEvent);

	// 如果需要同时输入字符文本
	if (!AdditionalText.IsEmpty())
	{
		for (const TCHAR Ch : AdditionalText)
		{
			FCharacterEvent CharEvent(Ch, Modifiers, 0, false);
			FSlateApplication::Get().ProcessKeyCharEvent(CharEvent);
		}
	}

	FKeyEvent KeyUpEvent(Key, Modifiers, 0, false, 0, 0);
	FSlateApplication::Get().ProcessKeyUpEvent(KeyUpEvent);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"), true);
	Result->SetStringField(TEXT("key"),     KeyStr);
	Result->SetBoolField  (TEXT("handled"), bHandled);
	return Result;
}

// ─────────────────────────────────────────────────────────────────────────────
// 内部辅助：新增功能共用
// ─────────────────────────────────────────────────────────────────────────────

/** 根据 window_index / window_title 参数定位目标窗口，找不到则返回第一个可见正常窗口 */
static TSharedPtr<SWindow> FindTargetWindow(const TSharedPtr<FJsonObject>& Params)
{
	const TArray<TSharedRef<SWindow>>& TopWindows = FSlateApplication::Get().GetTopLevelWindows();
	if (TopWindows.IsEmpty()) return nullptr;

	double WindowIndexD = -1.0;
	Params->TryGetNumberField(TEXT("window_index"), WindowIndexD);
	int32 WindowIndex = static_cast<int32>(WindowIndexD);
	if (WindowIndex >= 0 && WindowIndex < TopWindows.Num())
		return TopWindows[WindowIndex];

	FString WindowTitle;
	if (Params->TryGetStringField(TEXT("window_title"), WindowTitle) && !WindowTitle.IsEmpty())
	{
		for (const TSharedRef<SWindow>& Win : TopWindows)
		{
			if (Win->GetTitle().ToString().Contains(WindowTitle))
				return Win;
		}
	}

	for (const TSharedRef<SWindow>& Win : TopWindows)
	{
		if (Win->IsVisible() && Win->GetType() == EWindowType::Normal)
			return Win;
	}
	return TopWindows[0];
}

/** SWindow -> JSON 摘要 */
static TSharedPtr<FJsonObject> WindowToJsonSummary(const TSharedRef<SWindow>& Win)
{
	auto Obj = MakeShared<FJsonObject>();
	Obj->SetStringField(TEXT("title"),   Win->GetTitle().ToString());
	Obj->SetStringField(TEXT("type"),    WindowTypeToString(Win->GetType()));
	Obj->SetBoolField  (TEXT("visible"), Win->IsVisible());
	const FVector2D Pos  = Win->GetPositionInScreen();
	const FVector2D Size = Win->GetSizeInScreen();
	Obj->SetNumberField(TEXT("x"),      Pos.X);
	Obj->SetNumberField(TEXT("y"),      Pos.Y);
	Obj->SetNumberField(TEXT("width"),  Size.X);
	Obj->SetNumberField(TEXT("height"), Size.Y);
	return Obj;
}

/** ETabRole -> 可读字符串 */
static FString TabRoleToString(ETabRole Role)
{
	switch (Role)
	{
	case ETabRole::MajorTab:    return TEXT("MajorTab");
	case ETabRole::PanelTab:    return TEXT("PanelTab");
	case ETabRole::DocumentTab: return TEXT("DocumentTab");
	case ETabRole::NomadTab:    return TEXT("NomadTab");
	default:                    return TEXT("Unknown");
	}
}

/** 递归收集 Widget 树中所有的 SDockTab */
static void FindDockTabsRecursive(
	TSharedPtr<SWidget>               Widget,
	TArray<TSharedPtr<FJsonValue>>&   OutTabs,
	const FString&                    WindowTitle,
	int32 MaxDepth, int32 CurrentDepth)
{
	if (!Widget.IsValid() || CurrentDepth > MaxDepth) return;

	if (Widget->GetType() == FName(TEXT("SDockTab")))
	{
		TSharedPtr<SDockTab> DockTab = StaticCastSharedPtr<SDockTab>(Widget);
		if (DockTab.IsValid())
		{
			auto TabObj = MakeShared<FJsonObject>();
			TabObj->SetStringField(TEXT("label"),        DockTab->GetTabLabel().ToString());
			TabObj->SetStringField(TEXT("role"),         TabRoleToString(DockTab->GetTabRole()));
			TabObj->SetBoolField  (TEXT("is_foreground"),DockTab->IsForeground());
			TabObj->SetStringField(TEXT("in_window"),    WindowTitle);
			OutTabs.Add(MakeShared<FJsonValueObject>(TabObj));
		}
	}

	FChildren* Children = Widget->GetChildren();
	if (Children)
	{
		for (int32 i = 0; i < Children->Num(); ++i)
		{
			FindDockTabsRecursive(Children->GetChildAt(i), OutTabs, WindowTitle, MaxDepth, CurrentDepth + 1);
		}
	}
}

/** 递归查找并关闭 DockTab（按 label 或 tab_id 匹配） */
static bool CloseDockTabRecursive(
	TSharedPtr<SWidget> Widget,
	const FString& TabLabelFilter,
	const FString& TabIdFilter,
	FString& OutClosedLabel,
	FString& OutClosedTabId)
{
	if (!Widget.IsValid())
		return false;

	if (Widget->GetType() == FName(TEXT("SDockTab")))
	{
		TSharedPtr<SDockTab> DockTab = StaticCastSharedPtr<SDockTab>(Widget);
		if (DockTab.IsValid())
		{
			const FString Label = DockTab->GetTabLabel().ToString();
			const FString TabId = DockTab->GetLayoutIdentifier().ToString();
			const bool bLabelMatch = !TabLabelFilter.IsEmpty() && Label.Contains(TabLabelFilter);
			const bool bIdMatch = !TabIdFilter.IsEmpty() && TabId.Contains(TabIdFilter);
			if (bLabelMatch || bIdMatch)
			{
				if (DockTab->RequestCloseTab())
				{
					OutClosedLabel = Label;
					OutClosedTabId = TabId;
					return true;
				}
			}
		}
	}

	FChildren* Children = Widget->GetChildren();
	if (Children)
	{
		for (int32 i = 0; i < Children->Num(); ++i)
		{
			if (CloseDockTabRecursive(Children->GetChildAt(i), TabLabelFilter, TabIdFilter, OutClosedLabel, OutClosedTabId))
				return true;
		}
	}
	return false;
}

// ─────────────────────────────────────────────────────────────────────────────
// 窗口管理
// ─────────────────────────────────────────────────────────────────────────────

FJsonObjectParameter UMCPSlateTools::HandleGetActiveWindow(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	TSharedPtr<SWindow> ActiveWindow = FSlateApplication::Get().GetActiveTopLevelWindow();
	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	if (!ActiveWindow.IsValid())
	{
		Result->SetBoolField  (TEXT("success"), false);
		Result->SetStringField(TEXT("error"),   TEXT("No active top-level window"));
		return Result;
	}

	Result->SetBoolField(TEXT("success"), true);
	Result->SetObjectField(TEXT("window"), WindowToJsonSummary(ActiveWindow.ToSharedRef()));
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleMoveWindow(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	double X = 0.0, Y = 0.0;
	if (!Params->TryGetNumberField(TEXT("x"), X) || !Params->TryGetNumberField(TEXT("y"), Y))
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'x' or 'y' parameter"));

	TSharedPtr<SWindow> Win = FindTargetWindow(Params);
	if (!Win.IsValid())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Target window not found"));

	Win->MoveWindowTo(FVector2D(X, Y));

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"), true);
	Result->SetStringField(TEXT("window_title"), Win->GetTitle().ToString());
	Result->SetNumberField(TEXT("new_x"),        X);
	Result->SetNumberField(TEXT("new_y"),        Y);
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleResizeWindow(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	double W = 0.0, H = 0.0;
	if (!Params->TryGetNumberField(TEXT("width"), W) || !Params->TryGetNumberField(TEXT("height"), H))
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'width' or 'height' parameter"));

	TSharedPtr<SWindow> Win = FindTargetWindow(Params);
	if (!Win.IsValid())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Target window not found"));

	Win->Resize(FVector2D(W, H));

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"),      true);
	Result->SetStringField(TEXT("window_title"), Win->GetTitle().ToString());
	Result->SetNumberField(TEXT("new_width"),     W);
	Result->SetNumberField(TEXT("new_height"),    H);
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleCloseWindow(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	TSharedPtr<SWindow> Win = FindTargetWindow(Params);
	if (!Win.IsValid())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Target window not found"));

	const FString Title = Win->GetTitle().ToString();
	FSlateApplication::Get().RequestDestroyWindow(Win.ToSharedRef());

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"),       true);
	Result->SetStringField(TEXT("closed_window"), Title);
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleCloseDockTab(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	FString TabLabel;
	FString TabId;
	Params->TryGetStringField(TEXT("tab_label"), TabLabel);
	Params->TryGetStringField(TEXT("tab_id"),    TabId);
	if (TabLabel.IsEmpty() && TabId.IsEmpty())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'tab_label' or 'tab_id' parameter"));

	FString WindowTitleFilter;
	Params->TryGetStringField(TEXT("window_title"), WindowTitleFilter);

	const TArray<TSharedRef<SWindow>>& TopWindows = FSlateApplication::Get().GetTopLevelWindows();
	if (TopWindows.IsEmpty())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No top-level windows found"));

	FString ClosedLabel;
	FString ClosedTabId;
	for (const TSharedRef<SWindow>& Win : TopWindows)
	{
		if (!WindowTitleFilter.IsEmpty() && !Win->GetTitle().ToString().Contains(WindowTitleFilter))
			continue;

		if (CloseDockTabRecursive(Win->GetContent(), TabLabel, TabId, ClosedLabel, ClosedTabId))
		{
			FJsonObjectParameter Result = MakeShared<FJsonObject>();
			Result->SetBoolField  (TEXT("success"),   true);
			Result->SetStringField(TEXT("tab_label"), ClosedLabel);
			Result->SetStringField(TEXT("tab_id"),    ClosedTabId);
			Result->SetStringField(TEXT("in_window"), Win->GetTitle().ToString());
			return Result;
		}
	}

	return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("DockTab not found"));
}

// ─────────────────────────────────────────────────────────────────────────────
// 焦点管理
// ─────────────────────────────────────────────────────────────────────────────

FJsonObjectParameter UMCPSlateTools::HandleGetFocusedWidget(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	TSharedPtr<SWidget> FocusedWidget = FSlateApplication::Get().GetKeyboardFocusedWidget();

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	if (!FocusedWidget.IsValid())
	{
		Result->SetBoolField  (TEXT("success"), false);
		Result->SetStringField(TEXT("error"),   TEXT("No widget currently has keyboard focus"));
		return Result;
	}

	Result->SetBoolField  (TEXT("success"),   true);
	Result->SetStringField(TEXT("type"),      FocusedWidget->GetType().ToString());
	Result->SetStringField(TEXT("tag"),       FocusedWidget->GetTag().ToString());
	Result->SetStringField(TEXT("type_name"), FocusedWidget->GetTypeAsString());

	// 尝试获取文本内容
	if (FocusedWidget->GetType() == FName(TEXT("STextBlock")))
	{
		TSharedPtr<STextBlock> TB = StaticCastSharedPtr<STextBlock>(FocusedWidget);
		if (TB.IsValid())
			Result->SetStringField(TEXT("text"), TB->GetText().ToString());
	}
	else if (FocusedWidget->GetType() == FName(TEXT("SEditableText")))
	{
		TSharedPtr<SEditableText> ET = StaticCastSharedPtr<SEditableText>(FocusedWidget);
		if (ET.IsValid())
			Result->SetStringField(TEXT("text"), ET->GetText().ToString());
	}
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleSetKeyboardFocus(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	double X = 0.0, Y = 0.0;
	if (!Params->TryGetNumberField(TEXT("x"), X) || !Params->TryGetNumberField(TEXT("y"), Y))
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'x' or 'y' parameter"));

	const FVector2f Pos(static_cast<float>(X), static_cast<float>(Y));
	const TArray<TSharedRef<SWindow>>& Windows = FSlateApplication::Get().GetTopLevelWindows();
	FWidgetPath WidgetPath = FSlateApplication::Get().LocateWindowUnderMouse(Pos, Windows, true);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	if (!WidgetPath.IsValid())
	{
		Result->SetBoolField  (TEXT("success"), false);
		Result->SetStringField(TEXT("error"),   TEXT("No widget found at the given position"));
		return Result;
	}

	FSlateApplication::Get().SetKeyboardFocus(
		WidgetPath.GetLastWidget().ToSharedPtr(), EFocusCause::SetDirectly);

	Result->SetBoolField  (TEXT("success"),       true);
	Result->SetNumberField(TEXT("x"),             X);
	Result->SetNumberField(TEXT("y"),             Y);
	Result->SetStringField(TEXT("focused_widget"), WidgetPath.GetLastWidget()->GetType().ToString());
	return Result;
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab / 面板管理
// ─────────────────────────────────────────────────────────────────────────────

FJsonObjectParameter UMCPSlateTools::HandleInvokeTab(const FJsonObjectParameter& Params)
{
	FString TabIdStr;
	if (!Params->TryGetStringField(TEXT("tab_id"), TabIdStr) || TabIdStr.IsEmpty())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'tab_id' parameter"));

	TSharedPtr<SDockTab> Tab = FGlobalTabmanager::Get()->TryInvokeTab(FTabId(*TabIdStr));

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	if (!Tab.IsValid())
	{
		Result->SetBoolField  (TEXT("success"), false);
		Result->SetStringField(TEXT("error"),
			FString::Printf(TEXT("Tab '%s' could not be invoked. "
				"Common IDs: OutputLog, ContentBrowser1, LevelEditor, "
				"WorldOutliner, DetailsView"), *TabIdStr));
		return Result;
	}

	Result->SetBoolField  (TEXT("success"),     true);
	Result->SetStringField(TEXT("tab_id"),      TabIdStr);
	Result->SetStringField(TEXT("tab_label"),   Tab->GetTabLabel().ToString());
	Result->SetStringField(TEXT("tab_role"),    TabRoleToString(Tab->GetTabRole()));
	Result->SetBoolField  (TEXT("is_foreground"), Tab->IsForeground());
	return Result;
}

FJsonObjectParameter UMCPSlateTools::HandleGetAllDockTabs(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	TArray<TSharedPtr<FJsonValue>> AllTabs;
	for (const TSharedRef<SWindow>& Win : FSlateApplication::Get().GetTopLevelWindows())
	{
		FindDockTabsRecursive(Win->GetContent(), AllTabs, Win->GetTitle().ToString(), 20, 0);
	}

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"), true);
	Result->SetArrayField (TEXT("tabs"),    AllTabs);
	Result->SetNumberField(TEXT("count"),   AllTabs.Num());
	return Result;
}

// ─────────────────────────────────────────────────────────────────────────────
// 滚动
// ─────────────────────────────────────────────────────────────────────────────

FJsonObjectParameter UMCPSlateTools::HandleScrollAtPosition(const FJsonObjectParameter& Params)
{
	if (!FSlateApplication::IsInitialized())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SlateApplication not initialized"));

	double X = 0.0, Y = 0.0, Delta = 0.0;
	if (!Params->TryGetNumberField(TEXT("x"), X) || !Params->TryGetNumberField(TEXT("y"), Y))
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'x' or 'y' parameter"));
	if (!Params->TryGetNumberField(TEXT("delta"), Delta))
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'delta' parameter"));

	const FVector2f ScrollPos(static_cast<float>(X), static_cast<float>(Y));
	const float     WheelDelta = static_cast<float>(Delta);

	FPointerEvent WheelEvent(
		0,
		ScrollPos, ScrollPos,
		TSet<FKey>(),
		WheelDelta > 0.f ? EKeys::MouseScrollUp : EKeys::MouseScrollDown,
		WheelDelta,
		FModifierKeysState());

	FSlateApplication::Get().ProcessMouseWheelOrGestureEvent(WheelEvent, nullptr);

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"), true);
	Result->SetNumberField(TEXT("x"),       X);
	Result->SetNumberField(TEXT("y"),       Y);
	Result->SetNumberField(TEXT("delta"),   Delta);
	return Result;
}

// ─────────────────────────────────────────────────────────────────────────────
// 通知
// ─────────────────────────────────────────────────────────────────────────────

FJsonObjectParameter UMCPSlateTools::HandleShowNotification(const FJsonObjectParameter& Params)
{
	FString Message;
	if (!Params->TryGetStringField(TEXT("message"), Message) || Message.IsEmpty())
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'message' parameter"));

	FString TypeStr = TEXT("Info");
	Params->TryGetStringField(TEXT("type"), TypeStr);

	double DurationD = 3.0;
	Params->TryGetNumberField(TEXT("duration"), DurationD);

	bool bWithButton = false;
	Params->TryGetBoolField(TEXT("with_button"), bWithButton);

	FNotificationInfo Info(FText::FromString(Message));
	Info.bFireAndForget  = !bWithButton;
	Info.ExpireDuration  = static_cast<float>(DurationD);
	Info.FadeOutDuration = 1.0f;
	Info.bUseLargeFont   = false;

	if (bWithButton)
	{
		FNotificationButtonInfo DismissBtn(
			FText::FromString(TEXT("Dismiss")),
			FText(),
			FSimpleDelegate::CreateLambda([]{}),
			SNotificationItem::CS_None);
		Info.ButtonDetails.Add(DismissBtn);
	}

	TSharedPtr<SNotificationItem> Item = FSlateNotificationManager::Get().AddNotification(Info);

	if (Item.IsValid())
	{
		SNotificationItem::ECompletionState State = SNotificationItem::CS_None;
		if      (TypeStr == TEXT("Success")) State = SNotificationItem::CS_Success;
		else if (TypeStr == TEXT("Failure")) State = SNotificationItem::CS_Fail;
		else if (TypeStr == TEXT("Pending")) State = SNotificationItem::CS_Pending;
		Item->SetCompletionState(State);
	}

	FJsonObjectParameter Result = MakeShared<FJsonObject>();
	Result->SetBoolField  (TEXT("success"),  Item.IsValid());
	Result->SetStringField(TEXT("message"),  Message);
	Result->SetStringField(TEXT("type"),     TypeStr);
	Result->SetNumberField(TEXT("duration"), DurationD);
	return Result;
}
