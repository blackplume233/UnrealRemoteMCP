// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Structure/JsonParameter.h"
#include "UObject/Object.h"
#include "MCPUMGTools.generated.h"

/**
 * rReference https://github.com/chongdashu/unreal-mcp
 */
UCLASS()
class REMOTEMCP_API UMCPUMGTools : public UObject
{
	GENERATED_BODY()
public:
	    /**
     * Create a new UMG Widget Blueprint
     * @param Params - Must include "name" for the blueprint name
     * @return JSON response with the created blueprint details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static
    FJsonObjectParameter HandleCreateUMGWidgetBlueprint(const FJsonObjectParameter& Params);

    /**
     * Add a Text Block widget to a UMG Widget Blueprint
     * @param Params - Must include:
     *                "blueprint_name" - Name of the target Widget Blueprint
     *                "widget_name" - Name for the new Text Block
     *                "text" - Initial text content (optional)
     *                "position" - [X, Y] position in the canvas (optional)
     * @return JSON response with the added widget details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static 
    FJsonObjectParameter HandleAddTextBlockToWidget(const FJsonObjectParameter& Params);

    /**
     * Add a widget instance to the game viewport
     * @param Params - Must include:
     *                "blueprint_name" - Name of the Widget Blueprint to instantiate
     *                "z_order" - Z-order for widget display (optional)
     * @return JSON response with the widget instance details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static
    FJsonObjectParameter HandleAddWidgetToViewport(const FJsonObjectParameter& Params);

    /**
     * Add a Button widget to a UMG Widget Blueprint
     * @param Params - Must include:
     *                "blueprint_name" - Name of the target Widget Blueprint
     *                "widget_name" - Name for the new Button
     *                "text" - Button text
     *                "position" - [X, Y] position in the canvas
     * @return JSON response with the added widget details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static 
    FJsonObjectParameter HandleAddButtonToWidget(const FJsonObjectParameter& Params);

    /**
     * Bind an event to a widget (e.g. button click)
     * @param Params - Must include:
     *                "blueprint_name" - Name of the target Widget Blueprint
     *                "widget_name" - Name of the widget to bind
     *                "event_name" - Name of the event to bind
     * @return JSON response with the binding details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint") static
    FJsonObjectParameter HandleBindWidgetEvent(const FJsonObjectParameter& Params);

    /**
     * Set up text block binding for dynamic updates
     * @param Params - Must include:
     *                "blueprint_name" - Name of the target Widget Blueprint
     *                "widget_name" - Name of the widget to bind
     *                "binding_name" - Name of the binding to set up
     * @return JSON response with the binding details
     */
	UFUNCTION(BlueprintCallable, Category = "MCP|Blueprint")
    static FJsonObjectParameter HandleSetTextBlockBinding(const FJsonObjectParameter& Params);
};
