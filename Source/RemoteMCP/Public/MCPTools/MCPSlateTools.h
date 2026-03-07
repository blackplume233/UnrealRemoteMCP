// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Layout/WidgetPath.h"
#include "MCPSlateTools.generated.h"

/**
 * 通过 MCP 协议查询和操作 Slate UI 界面的工具集
 * 支持：遍历 Widget 树、查询窗口信息、模拟鼠标/键盘交互
 */
UCLASS()
class REMOTEMCP_API UMCPSlateTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * 获取所有顶层窗口的基本信息（标题、类型、位置、大小）
	 * @param Params - 无必填参数
	 * @return 窗口列表 JSON
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetAllWindows(const FJsonObjectParameter& Params);

	/**
	 * 获取指定窗口的 Widget 树结构
	 * @param Params - 可选: window_index(int), window_title(string), max_depth(int, 默认5)
	 *               不指定窗口时默认取第一个可见窗口
	 * @return Widget 树 JSON
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetWidgetTree(const FJsonObjectParameter& Params);

	/**
	 * 获取当前鼠标光标位置下的 Widget 路径及几何信息
	 * @param Params - 无必填参数
	 * @return Widget 路径 JSON（从窗口根到最终 Widget 的完整层级）
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetWidgetUnderCursor(const FJsonObjectParameter& Params);

	/**
	 * 在所有（或指定）窗口中按 Widget 类型名称搜索 Widget
	 * @param Params - 必填: type_name(string), 可选: window_index(int), window_title(string), max_depth(int, 默认8)
	 * @return 匹配的 Widget 列表（含文本、tag、所属窗口信息）
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleFindWidgetsByType(const FJsonObjectParameter& Params);

	/**
	 * 在指定屏幕坐标模拟鼠标点击
	 * @param Params - 必填: x(float), y(float), 可选: button("Left"/"Right"/"Middle", 默认"Left")
	 * @return 操作结果及被点击 Widget 类型
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleClickAtPosition(const FJsonObjectParameter& Params);

	/**
	 * 向当前焦点 Widget 发送文本输入（逐字符发送 char 事件）
	 * @param Params - 必填: text(string)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleSendTextInput(const FJsonObjectParameter& Params);

	/**
	 * 发送键盘按键（支持 Enter、Escape、Tab、Delete 等功能键及组合键）
	 * @param Params - 必填: key(string, 如"Enter"/"Escape"/"Tab"/"Delete"/"A"等)
	 *               可选: shift(bool), ctrl(bool), alt(bool)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleSendKeyPress(const FJsonObjectParameter& Params);

	/**
	 * 获取指定屏幕坐标处的 Widget 信息（不需要移动鼠标光标）
	 * @param Params - 必填: x(float), y(float)
	 * @return 该坐标下的 Widget 路径 JSON
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetWidgetAtPosition(const FJsonObjectParameter& Params);

	// ─── 窗口管理 ───────────────────────────────────────────────────────────

	/**
	 * 获取当前激活的顶层窗口详情
	 * @param Params - 无必填参数
	 * @return 激活窗口的 JSON（标题/位置/大小/类型）
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetActiveWindow(const FJsonObjectParameter& Params);

	/**
	 * 移动指定窗口到新的屏幕位置
	 * @param Params - 必填: x(float), y(float)，可选: window_index(int), window_title(string)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleMoveWindow(const FJsonObjectParameter& Params);

	/**
	 * 调整指定窗口的大小
	 * @param Params - 必填: width(float), height(float)，可选: window_index(int), window_title(string)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleResizeWindow(const FJsonObjectParameter& Params);

	/**
	 * 关闭（销毁）指定窗口
	 * @param Params - 可选: window_index(int), window_title(string)，均不填则关闭当前激活窗口
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleCloseWindow(const FJsonObjectParameter& Params);

	/**
	 * 关闭指定 DockTab（如 Project Settings、Plugins 等面板）
	 * @param Params - 必填: tab_label(string) 或 tab_id(string)
	 *               可选: window_title(string)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleCloseDockTab(const FJsonObjectParameter& Params);

	// ─── 焦点管理 ───────────────────────────────────────────────────────────

	/**
	 * 获取当前键盘焦点所在的 Widget 信息
	 * @param Params - 无必填参数
	 * @return 焦点 Widget 的 type/tag/文本 JSON
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetFocusedWidget(const FJsonObjectParameter& Params);

	/**
	 * 将键盘焦点设置到指定屏幕坐标处的 Widget
	 * @param Params - 必填: x(float), y(float)
	 * @return 操作结果及被聚焦的 Widget 类型
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleSetKeyboardFocus(const FJsonObjectParameter& Params);

	// ─── Tab / 面板管理 ─────────────────────────────────────────────────────

	/**
	 * 通过 Tab ID 打开或切换到指定 Editor 面板
	 * 常用 Tab ID: "OutputLog", "ContentBrowser1", "LevelEditor", "WorldOutliner",
	 *              "DetailsView", "Sequencer", "MaterialEditor", "BlueprintEditor"
	 * @param Params - 必填: tab_id(string)
	 * @return 操作结果及打开的 Tab 标题
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleInvokeTab(const FJsonObjectParameter& Params);

	/**
	 * 获取所有当前打开的 Dock Tab 列表（遍历 Widget 树中的 SDockTab）
	 * @param Params - 无必填参数
	 * @return Tab 列表 JSON，每项含 label/role/is_foreground/in_window
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleGetAllDockTabs(const FJsonObjectParameter& Params);

	// ─── 滚动 ───────────────────────────────────────────────────────────────

	/**
	 * 在指定屏幕坐标模拟鼠标滚轮滚动
	 * @param Params - 必填: x(float), y(float), delta(float, 正=向上/向前, 负=向下/向后)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleScrollAtPosition(const FJsonObjectParameter& Params);

	// ─── 通知 ───────────────────────────────────────────────────────────────

	/**
	 * 在编辑器右下角弹出 Slate 通知气泡
	 * @param Params - 必填: message(string)
	 *               可选: type("Info"/"Success"/"Pending"/"Failure", 默认"Info")
	 *                     duration(float, 显示秒数, 默认3.0)
	 *                     with_button(bool, 是否带关闭按钮, 默认false)
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Slate")
	static FJsonObjectParameter HandleShowNotification(const FJsonObjectParameter& Params);

private:
	/** 递归将 Widget 转换为 JSON 节点，children 按 max_depth 截断 */
	static TSharedPtr<FJsonObject> WidgetToJson(TSharedRef<SWidget> Widget, int32 MaxDepth, int32 CurrentDepth);

	/** 递归在 Widget 树中按类型名搜索，结果追加到 OutArray */
	static void FindWidgetsByTypeRecursive(
		TSharedPtr<SWidget> Widget,
		const FName& TypeName,
		const FString& WindowTitle,
		TArray<TSharedPtr<FJsonValue>>& OutArray,
		int32 MaxDepth,
		int32 CurrentDepth);

	/** 构建 Widget 路径数组（FWidgetPath -> JSON array）*/
	static TArray<TSharedPtr<FJsonValue>> WidgetPathToJsonArray(const FWidgetPath& WidgetPath);
};
