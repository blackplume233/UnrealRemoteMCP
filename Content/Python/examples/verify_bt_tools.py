import time
import unreal
from foundation import global_context


# AI(GPT-5.2): 说明
# - 旧版本示例依赖 unreal.MCPPythonBridge.call_tool，但该接口在当前工程中不可用。
# - 新版本通过 global_context.get_mcp_instance().call_tool(...) 直接调用 FastMCP 工具。
# - 该脚本适合配合 MCP 工具 run_python_script_async 执行（其会 await 顶层变量 result）。


async def verify_bt_tools():
    print("=== Starting Behavior Tree Tools Verification ===")
    mcp = global_context.get_mcp_instance()

    suffix = time.strftime("%Y%m%d_%H%M%S")
    pkg = "/Game/VerifyTest/"
    bb_name = f"BB_VerifyTest_{suffix}"
    bt_name = f"BT_VerifyTest_{suffix}"

    # 1. Create Blackboard
    print("\n1. Creating Blackboard...")
    bb_res = await mcp.call_tool("bt_create_blackboard", {"name": bb_name, "package_path": pkg})
    print(f"Result: {bb_res}")

    # 2. Create Behavior Tree
    print("\n2. Creating Behavior Tree...")
    bt_res = await mcp.call_tool("bt_create_asset", {"name": bt_name, "package_path": pkg})
    print(f"Result: {bt_res}")

    bt_path = (bt_res or {}).get("path")
    if not bt_path:
        print("Failed to create BT asset. Aborting.")
        return {"ok": False, "stage": "bt_create_asset", "bt_res": bt_res}

    # 3. Get Graph (now auto-ensures graph existence in C++)
    print("\n3. Getting Graph Path...")
    graph_res = await mcp.call_tool("bt_get_graph", {"bt_path": bt_path})
    print(f"Result: {graph_res}")

    graph_path = (graph_res or {}).get("graph_path")
    if not graph_path:
        print("Failed to get graph path. Aborting.")
        return {"ok": False, "stage": "bt_get_graph", "graph_res": graph_res}

    # 4. Add Nodes
    print("\n4. Adding Nodes...")
    selector_res = await mcp.call_tool(
        "bt_add_node",
        {"graph_path": graph_path, "node_class": "Composite_Selector", "pos_x": 250, "pos_y": 0},
    )
    print(f"Selector Node: {selector_res}")

    wait_res = await mcp.call_tool(
        "bt_add_node",
        {"graph_path": graph_path, "node_class": "Task_Wait", "pos_x": 500, "pos_y": 120},
    )
    print(f"Wait Node: {wait_res}")

    selector_path = (((selector_res or {}).get("data") or {}).get("node") or {}).get("path")
    wait_path = (((wait_res or {}).get("data") or {}).get("node") or {}).get("path")
    if not selector_path or not wait_path:
        print("Failed to add nodes. Aborting.")
        return {"ok": False, "stage": "bt_add_node", "selector_res": selector_res, "wait_res": wait_res}

    # 5. Connect Nodes: Root -> Selector -> Wait
    print("\n5. Listing nodes and connecting...")
    nodes_res = await mcp.call_tool("bt_list_graph_nodes", {"graph_path": graph_path})
    nodes = (((nodes_res or {}).get("data") or {}).get("nodes") or [])
    root_path = ""
    for n in nodes:
        if (n.get("class") or "").endswith("_Root"):
            root_path = n.get("path") or ""
            break
    if not root_path:
        return {"ok": False, "stage": "bt_list_graph_nodes", "nodes_res": nodes_res}

    conn1 = await mcp.call_tool("bt_connect_nodes", {"graph_path": graph_path, "parent_node_path": root_path, "child_node_path": selector_path})
    conn2 = await mcp.call_tool("bt_connect_nodes", {"graph_path": graph_path, "parent_node_path": selector_path, "child_node_path": wait_path})
    print(f"Root->Selector: {conn1}")
    print(f"Selector->Wait: {conn2}")

    # 6. Verify Auxiliary Nodes tool still works
    print("\n6. Checking Auxiliary Nodes...")
    aux_res = await mcp.call_tool("bt_get_auxiliary_nodes", {"node_path": wait_path})
    print(f"Aux Nodes: {aux_res}")

    print("\n=== Verification Complete ===")
    return {"ok": True, "bt_path": bt_path, "graph_path": graph_path, "root": root_path, "selector": selector_path, "wait": wait_path}


# For run_python_script_async:
result = verify_bt_tools()
