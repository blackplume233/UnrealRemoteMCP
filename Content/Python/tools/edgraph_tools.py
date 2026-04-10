from __future__ import annotations

import os
from typing import Any, Dict

import unreal
from foundation.mcp_app import UnrealMCP
from foundation.utility import call_cpp_tools


def register_edgraph_tools(mcp: UnrealMCP):
    """
    通用 EdGraph CRUD 工具。
    底层操作全部委托给 C++ UMCPEdGraphTools（绕过 Python 侧 Nodes/Pins protected 限制）。
    """

    mcp.set_domain_description(
        "edgraph",
        "通用 EdGraph 底层操作：发现图、节点增删改查、pin 连线枚举/连接/断开、编译诊断、资产元信息。支持 Blueprint/AnimBP/LBP/BT/HTN 等所有图类型。",
    )

    @mcp.domain_tool("edgraph")
    def edgraph_api_reference() -> Dict[str, Any]:
        """
        获取 EdGraph C++ 工具的 API 帮助信息。
        返回所有可用的 MCPEdGraphTools C++ 函数列表、参数格式、ImportText 速查表和调用示例。
        在需要对 Blueprint / AnimBP / LBP / BT / HTN 等图表进行增删改查操作时，
        调用此工具获取参考信息。
        """
        doc_path = os.path.join(os.path.dirname(__file__), "edgraph_api_reference.md")
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {"status": "error", "message": f"Failed to read API reference: {e}"}
        return {"status": "success", "data": {"reference": content}}

    @mcp.domain_tool("edgraph")
    def edgraph_find_graphs_in_asset(asset_path: str, name_filter: str = "", max_results: int = 50) -> Dict[str, Any]:
        """
        在指定资产里发现所有 EdGraph（支持 Blueprint、BehaviorTree 等多种资产类型）。

        Args:
            asset_path: 资产路径（/Game/...）
            name_filter: 可选，按 graph path/name 包含过滤（不区分大小写）
            max_results: 最多返回多少个
        """
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_find_graphs_in_asset, {
            "asset_path": asset_path,
            "name_filter": name_filter,
            "max_results": max_results,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_list_nodes(graph_path: str, include_properties: bool = False) -> Dict[str, Any]:
        """列出图内所有节点及其 pin 信息。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_list_graph_nodes, {
            "graph_path": graph_path,
            "include_properties": include_properties,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_get_node(
        graph_path: str,
        node_guid: str = "",
        node_name: str = "",
        node_path: str = "",
    ) -> Dict[str, Any]:
        """按 guid/name/path 查询单个节点（含详细 pin 信息）。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_get_graph_node, {
            "graph_path": graph_path,
            "node_guid": node_guid,
            "node_name": node_name,
            "node_path": node_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_delete_node(
        graph_path: str,
        node_guid: str = "",
        node_name: str = "",
        node_path: str = "",
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """从图内删除节点（先断开所有连线再移除）。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_delete_graph_node, {
            "graph_path": graph_path,
            "node_guid": node_guid,
            "node_name": node_name,
            "node_path": node_path,
            "auto_save_asset_path": auto_save_asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_set_node_properties(
        graph_path: str,
        properties: Any,
        node_guid: str = "",
        node_name: str = "",
        node_path: str = "",
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """
        修改节点属性（批量 set_editor_property）。

        properties: dict，键为属性名，值为要设置的值
        """
        if isinstance(properties, str):
            import json
            properties = json.loads(properties)
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_set_node_properties, {
            "graph_path": graph_path,
            "node_guid": node_guid,
            "node_name": node_name,
            "node_path": node_path,
            "properties": properties,
            "auto_save_asset_path": auto_save_asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_list_links(graph_path: str) -> Dict[str, Any]:
        """枚举图里所有 pin 连接（去重后输出）。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_list_graph_links, {
            "graph_path": graph_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_connect_pins(
        graph_path: str,
        from_node_guid: str,
        from_pin: str,
        to_node_guid: str,
        to_pin: str,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """连接两个 pin（优先使用 Schema.TryCreateConnection，降级 MakeLinkTo）。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_connect_pins, {
            "graph_path": graph_path,
            "from_node_guid": from_node_guid,
            "from_pin": from_pin,
            "to_node_guid": to_node_guid,
            "to_pin": to_pin,
            "auto_save_asset_path": auto_save_asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_disconnect_pin(
        graph_path: str,
        node_guid: str,
        pin_name: str,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """断开指定 pin 的所有连接。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_disconnect_pin, {
            "graph_path": graph_path,
            "node_guid": node_guid,
            "pin_name": pin_name,
            "auto_save_asset_path": auto_save_asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_add_comment(
        graph_path: str,
        comment: str,
        pos_x: float = 0,
        pos_y: float = 0,
        width: float = 400,
        height: float = 100,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """在图中添加一个 Comment 注释节点。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_add_comment_node, {
            "graph_path": graph_path,
            "comment": comment,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "width": width,
            "height": height,
            "auto_save_asset_path": auto_save_asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_add_node(
        graph_path: str,
        node_class: str,
        pos_x: float = 0,
        pos_y: float = 0,
        import_text: Any = None,
        pin_defaults: Any = None,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """
        在图中创建任意 UEdGraphNode 子类。

        Args:
            graph_path: 目标图的 UObject 路径
            node_class: 节点类名（如 K2Node_CallFunction, K2Node_IfThenElse）
            pos_x, pos_y: 节点位置
            import_text: dict，{PropertyName: "ImportText value"}，在 AllocateDefaultPins 前应用
            pin_defaults: dict，{PinName: "default value"}，在 AllocateDefaultPins 后应用
            auto_save_asset_path: 可选，创建后保存资产
        """
        params = {
            "graph_path": graph_path,
            "node_class": node_class,
            "pos_x": pos_x,
            "pos_y": pos_y,
        }
        if import_text is not None:
            if isinstance(import_text, str):
                import json as _json
                import_text = _json.loads(import_text)
            params["import_text"] = import_text
        if pin_defaults is not None:
            if isinstance(pin_defaults, str):
                import json as _json
                pin_defaults = _json.loads(pin_defaults)
            params["pin_defaults"] = pin_defaults
        if auto_save_asset_path:
            params["auto_save_asset_path"] = auto_save_asset_path
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_add_node, params)

    @mcp.domain_tool("edgraph")
    def edgraph_set_pin_default(
        graph_path: str,
        node_guid: str,
        pin_name: str,
        default_value: str = "",
        default_object: str = "",
        pin_direction: str = "",
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """
        设置/清除节点引脚的默认值。

        Args:
            graph_path: 图路径
            node_guid: 节点 GUID
            pin_name: 引脚名称
            default_value: 默认值的文本表示
            default_object: Object 类型引脚的资产路径
            pin_direction: "Input" 或 "Output"（用于同名引脚消歧）
        """
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_set_pin_default_value, {
            "graph_path": graph_path,
            "node_guid": node_guid,
            "pin_name": pin_name,
            "default_value": default_value,
            "default_object": default_object,
            "pin_direction": pin_direction,
            "auto_save_asset_path": auto_save_asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_compile(asset_path: str) -> Dict[str, Any]:
        """
        编译 Blueprint 资产并返回诊断信息。

        Returns: {status, has_error, messages[{severity, message}]}
        """
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_compile_asset, {
            "asset_path": asset_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_create_graph(
        asset_path: str,
        graph_name: str,
        graph_type: str = "function",
    ) -> Dict[str, Any]:
        """
        在 Blueprint 中创建函数或宏子图。

        Args:
            asset_path: Blueprint 资产路径
            graph_name: 新图名称
            graph_type: "function"（默认）或 "macro"
        """
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_create_graph, {
            "asset_path": asset_path,
            "graph_name": graph_name,
            "graph_type": graph_type,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_delete_graph(
        asset_path: str,
        graph_name: str = "",
        graph_path: str = "",
    ) -> Dict[str, Any]:
        """删除 Blueprint 中的子图（函数/宏）。"""
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_delete_graph, {
            "asset_path": asset_path,
            "graph_name": graph_name,
            "graph_path": graph_path,
        })

    @mcp.domain_tool("edgraph")
    def edgraph_get_asset_info(asset_path: str) -> Dict[str, Any]:
        """
        查询蓝图资产元数据：父类、变量、函数、接口、组件、所有图。

        Returns: {parent_class, variables[], functions[], interfaces[], components[], graphs[]}
        """
        return call_cpp_tools(unreal.MCPEdGraphTools.handle_get_asset_info, {
            "asset_path": asset_path,
        })
