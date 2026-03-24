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
