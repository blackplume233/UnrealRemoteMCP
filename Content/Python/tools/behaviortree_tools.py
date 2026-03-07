import unreal
import json
from foundation.mcp_app import UnrealMCP
from foundation.utility import like_str_parameter


def _to_json(params_dict):
    return json.dumps(params_dict)


def register_behaviortree_tools(mcp: UnrealMCP):
    """
    提供行为树(Behavior Tree)专用的编辑工具。
    结合 C++ Bridge (UMCPBehaviorTreeTools) 与通用 EdGraph 工具。
    """
    mcp.set_domain_description(
        "behaviortree",
        "行为树（Behavior Tree）资产编辑与节点操作：创建行为树/黑板、获取图、添加/连接节点、设置黑板与常见任务参数等。",
    )

    # AI(GPT-5.2): 说明
    # - 原文件存在同名工具函数重复定义（bt_create_asset/bt_create_blackboard/bt_get_auxiliary_nodes），会导致注册覆盖/冲突。
    # - 原 bt_add_node 为同步函数但调用 async 的 mcp.call_tool，返回 coroutine，MCP 无法序列化/消费。
    # - 这里统一成“一套工具定义”，优先走 C++ Bridge（MCPBehaviorTreeTools），无 bridge 时做安全 fallback。

    def _bridge_available() -> bool:
        return hasattr(unreal, "MCPBehaviorTreeTools")

    def _call_bridge_or_editor_tools(func_name: str, payload: dict):
        """
        AI(GPT-5.2): 统一封装 C++ Bridge / EditorTools 的调用，返回 json dict。
        """
        # AI(GPT-5.2): 关键兼容性修复
        # - 本插件的 Json 参数类型是 USTRUCT(FJsonObjectParameter)，其 JsonObjectFromString 不是 UFUNCTION，
        #   在 Python 中不可直接调用（也不存在 json_object_from_string）。
        # - 通过 C++ 暴露的 UMCPJsonUtils.MakeJsonObject() 在 C++ 内部完成 JsonObjectFromString，
        #   才能让 Params->TryGet*Field 正常工作。
        if not hasattr(unreal, "MCPJsonUtils"):
            return {"ok": False, "error": "MCPJsonUtils not found. Please compile/enable RemoteMCP plugin."}
        params = unreal.MCPJsonUtils.make_json_object(_to_json(payload))

        # 优先：MCPBehaviorTreeTools
        if _bridge_available():
            bridge = unreal.MCPBehaviorTreeTools
            if hasattr(bridge, func_name):
                res = getattr(bridge, func_name)(params)
                out_str = unreal.MCPJsonUtils.json_object_to_string(res)
                return json.loads(out_str) if out_str else {}

        # fallback：MCPEditorTools（历史实现）
        if hasattr(unreal, "MCPEditorTools") and hasattr(unreal.MCPEditorTools, func_name):
            res = getattr(unreal.MCPEditorTools, func_name)(params)
            out_str = unreal.MCPJsonUtils.json_object_to_string(res)
            return json.loads(out_str) if out_str else {}

        return {"ok": False, "error": f"Bridge/EditorTools function not found: {func_name}"}

    # AI(Claude Opus 4.5): 改为 domain_tool 注册，通过 get_dispatch/dispatch_tool 访问
    @mcp.domain_tool("behaviortree")
    def bt_get_graph(bt_path: str):
        """
        获取行为树资产内部的 Graph 对象路径。
        得到路径后，可以使用 edgraph_* 系列工具进一步操作节点。
        """
        bt_path = like_str_parameter(bt_path, "bt_path", "").strip()
        return _call_bridge_or_editor_tools("handle_get_behavior_tree_graph", {"bt_path": bt_path})

    @mcp.domain_tool("behaviortree")
    def bt_set_blackboard(bt_path: str, bb_path: str):
        """
        AI(GPT-5.2): 设置 BehaviorTree.BlackboardAsset（通过 C++ Bridge，避免 Python 侧属性受保护无法 set）。
        """
        bt_path = like_str_parameter(bt_path, "bt_path", "").strip()
        bb_path = like_str_parameter(bb_path, "bb_path", "").strip()
        return _call_bridge_or_editor_tools("handle_get_behavior_tree_graph", {"op": "set_blackboard", "bt_path": bt_path, "bb_path": bb_path})

    @mcp.domain_tool("behaviortree")
    def bt_set_wait_time(node_path: str, wait_time: float):
        """
        AI(GPT-5.2): 设置 BTTask_Wait 的 WaitTime（通过 C++ Bridge，绕开 Python 侧 NodeInstance 受保护无法访问）。
        """
        node_path = like_str_parameter(node_path, "node_path", "").strip()
        wait_time = float(wait_time) if wait_time is not None else 0.0
        return _call_bridge_or_editor_tools("handle_get_bt_auxiliary_nodes", {"op": "set_wait_time", "node_path": node_path, "wait_time": wait_time})

    @mcp.domain_tool("behaviortree")
    def bt_create_asset(name: str, package_path: str = "/Game/"):
        """创建新的行为树(Behavior Tree)资产。"""
        name = like_str_parameter(name, "name", "").strip()
        package_path = like_str_parameter(package_path, "package_path", "/Game/").strip()

        # 优先走 bridge；无 bridge 时 fallback 到 factory（不会依赖 bridge 的具体实现）
        if _bridge_available():
            return _call_bridge_or_editor_tools("handle_create_behavior_tree", {"name": name, "package_path": package_path})

        try:
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            factory = unreal.BehaviorTreeFactory()
            asset = asset_tools.create_asset(name, package_path, unreal.BehaviorTree, factory)
            if asset:
                return {"ok": True, "path": asset.get_path_name(), "name": asset.get_name()}
            return {"ok": False, "error": "Failed to create BehaviorTree via factory"}
        except Exception as e:
            return {"ok": False, "error": f"Failed to create BehaviorTree via factory: {str(e)}"}

    @mcp.domain_tool("behaviortree")
    def bt_create_blackboard(name: str, package_path: str = "/Game/"):
        """创建新的黑板(Blackboard)资产。"""
        name = like_str_parameter(name, "name", "").strip()
        package_path = like_str_parameter(package_path, "package_path", "/Game/").strip()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.BlackboardDataFactory()
        asset = asset_tools.create_asset(name, package_path, unreal.BlackboardData, factory)
        if asset:
            return {"ok": True, "path": asset.get_path_name(), "name": asset.get_name()}
        return {"ok": False, "error": "Failed to create Blackboard"}

    @mcp.domain_tool("behaviortree")
    def bt_get_auxiliary_nodes(node_path: str):
        """获取 BT 节点上挂载的辅助节点（Decorator 或 Service）。"""
        node_path = like_str_parameter(node_path, "node_path", "").strip()
        return _call_bridge_or_editor_tools("handle_get_bt_auxiliary_nodes", {"node_path": node_path})

    @mcp.domain_tool("behaviortree")
    def bt_list_graph_nodes(graph_path: str):
        """
        AI(GPT-5.2): 列出行为树 Graph 内所有节点（C++ Bridge，解决 Python 无法读取 Graph->Nodes 的问题）。
        """
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        # AI(GPT-5.2): 通过 handle_get_bt_auxiliary_nodes 的 op 多路复用实现（避免 LiveCoding 新增 UFUNCTION 需要重启）
        return _call_bridge_or_editor_tools("handle_get_bt_auxiliary_nodes", {"op": "list_nodes", "graph_path": graph_path})

    @mcp.domain_tool("behaviortree")
    def bt_connect_nodes(graph_path: str, parent_node_path: str, child_node_path: str):
        """
        AI(GPT-5.2): 连接行为树节点（父->子），默认用第0个输出 pin 连接到第0个输入 pin。
        """
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        parent_node_path = like_str_parameter(parent_node_path, "parent_node_path", "").strip()
        child_node_path = like_str_parameter(child_node_path, "child_node_path", "").strip()
        return _call_bridge_or_editor_tools(
            "handle_get_bt_auxiliary_nodes",
            {"op": "connect", "graph_path": graph_path, "parent_node_path": parent_node_path, "child_node_path": child_node_path},
        )

    @mcp.domain_tool("behaviortree")
    def bt_add_node(
        graph_path: str,
        node_class: str,
        bt_node_class: str = "",
        pos_x: int = 0,
        pos_y: int = 0,
        properties: str = "",
    ):
        """
        向行为树添加节点（Task/Composite）。

        AI(GPT-5.2): 这里不再依赖 Python 侧创建 BehaviorTreeGraphNode（Python 中这些类通常不可见），
        而是调用 C++ Bridge `HandleAddBTGraphNode`，通过设置 UAIGraphNode::ClassData 生成正确的 NodeInstance。
        """
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        node_class = like_str_parameter(node_class, "node_class", "").strip()
        bt_node_class = like_str_parameter(bt_node_class, "bt_node_class", "").strip()

        # AI(GPT-5.2): 优先使用 bt_node_class（反射式：可传 "/Script/AIModule.BTTask_Wait" 或 "BTTask_Wait" 等）
        # - 这样就不需要在 Python 侧维护 Task_/Composite_ 的字符串映射
        # - node_class 仅保留做向后兼容
        if not bt_node_class:
            # 兼容旧用法：Composite_Selector / Task_Wait / BTTask_* / BTComposite_*
            bt_node_class = node_class
            if node_class.startswith("Composite_"):
                bt_node_class = "BTComposite_" + node_class[len("Composite_") :]
            elif node_class.startswith("Task_"):
                bt_node_class = "BTTask_" + node_class[len("Task_") :]
            elif node_class.startswith(("BTTask_", "BTComposite_")):
                bt_node_class = node_class

        # 调用 C++ Bridge
        return _call_bridge_or_editor_tools(
            "handle_get_bt_auxiliary_nodes",
            {"op": "add_node", "graph_path": graph_path, "bt_node_class": bt_node_class, "pos_x": int(pos_x), "pos_y": int(pos_y)},
        )
