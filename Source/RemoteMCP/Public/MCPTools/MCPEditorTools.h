// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "UObject/Object.h"
#include "MCPEditorTools.generated.h"

/**
 * 提供编辑器工具函数的蓝图函数库
 * 这个类包含一系列用于远程控制Unreal编辑器的工具函数
 * 所有方法都使用JSON参数输入和输出，便于远程调用
 * Reference https://github.com/chongdashu/unreal-mcp
 */
UCLASS()
class REMOTEMCP_API UMCPEditorTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * 获取当前关卡中的所有Actor
	 * @param Params - 输入参数(不需要特定参数)
	 * @return 包含所有Actor信息的JSON对象
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleGetActorsInLevel(const FJsonObjectParameter& Params);
	
	/**
	 * 根据名称模式查找Actor
	 * @param Params - 输入参数，必须包含"pattern"字段
	 * @return 包含匹配Actor信息的JSON对象
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleFindActorsByName(const FJsonObjectParameter& Params);
	
	/**
	 * 在关卡中生成新的Actor
	 * @param Params - 输入参数，必须包含"type"和"name"字段，可选"location"、"rotation"和"scale"
	 * @return 新生成Actor的信息
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSpawnActor(const FJsonObjectParameter& Params);
	
	/**
	 * 删除指定名称的Actor
	 * @param Params - 输入参数，必须包含"name"字段
	 * @return 包含被删除Actor信息的JSON对象
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleDeleteActor(const FJsonObjectParameter& Params);
	
	/**
	 * 设置Actor的变换(位置、旋转、缩放)
	 * @param Params - 输入参数，必须包含"name"字段，可选"location"、"rotation"和"scale"
	 * @return 更新后Actor的信息
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetActorTransform(const FJsonObjectParameter& Params);
	
	/**
	 * 获取Actor的所有属性
	 * @param Params - 输入参数，必须包含"name"字段
	 * @return 包含Actor详细属性的JSON对象
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleGetActorProperties(const FJsonObjectParameter& Params);
	
	/**
	 * 设置Actor的特定属性
	 * @param Params - 输入参数，必须包含"name"、"property_name"和"property_value"字段
	 * @return 操作结果和更新后的Actor信息
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSetActorProperty(const FJsonObjectParameter& Params);

	/**
	 * 在关卡中生成蓝图Actor
	 * @param Params - 输入参数，必须包含"blueprint_name"和"actor_name"字段，可选"location"、"rotation"和"scale"
	 * @return 新生成蓝图Actor的信息
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleSpawnBlueprintActor(const FJsonObjectParameter& Params);

	/**
	 * 设置编辑器视口的焦点
	 * @param Params - 输入参数，必须包含"target"或"location"字段之一，可选"distance"和"orientation"
	 * @return 操作结果
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleFocusViewport(const FJsonObjectParameter& Params);
	
	/**
	 * 捕获编辑器视口的屏幕截图
	 * @param Params - 输入参数，必须包含"filepath"字段
	 * @return 包含截图文件路径的JSON对象
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
	static FJsonObjectParameter HandleTakeScreenshot(const FJsonObjectParameter& Params);
};
