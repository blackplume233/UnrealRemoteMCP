# 行为树端到端创建（可循环验证）

> AI(GPT-5.2) 记录：本文沉淀“从零创建 Blackboard + BehaviorTree，并在图上添加/连接节点，设置 BlackboardAsset，最后保存”的可复现流程。

## 前置条件

- UE 编辑器运行中，RemoteMCP 插件已编译并启动 MCP（可用 `mcp.reload` 热重载工具）。
- 已注册以下 MCP 工具（Python 层）：`bt_create_blackboard`, `bt_create_asset`, `bt_get_graph`, `bt_list_graph_nodes`, `bt_add_node`, `bt_connect_nodes`, `bt_set_blackboard`

> 说明：`bt_list_graph_nodes/bt_connect_nodes/bt_add_node` 的底层依赖 C++ Bridge 访问 `BehaviorTreeGraph->Nodes`（Python 侧该字段常为 protected 不可读）。

## 推荐流程（最小闭环）

### 1) 创建 Blackboard 与 BehaviorTree

- `bt_create_blackboard(name, package_path)`
- `bt_create_asset(name, package_path)`

返回示例字段：

- Blackboard：`{"ok": true, "path": "/Game/.../BB_xxx.BB_xxx"}`
- BT：`{"name": "...", "path": "/Game/.../BT_xxx.BT_xxx"}` 或 `{"success":false, "error":...}`

### 2) 获取 BT Graph（自动确保 Graph 存在）

- `bt_get_graph(bt_path)`

实现要点（C++）：若 BT 资产还没有生成 Graph，会 **自动 OpenEditorForAsset(BT)** 再扫描一次，尽量保证拿到 `BehaviorTreeGraph`。

返回：

- `{"graph_path": "...:Behavior Tree", "graph_name":"Behavior Tree"}`

### 3) 列出 Graph 节点（定位 Root）

- `bt_list_graph_nodes(graph_path)`

预期至少有 1 个 Root 节点（如 `BehaviorTreeGraphNode_Root_0`），并包含 pins（常见 Root 输出 pin 名为 `In`，方向 Output）。

### 4) 添加节点

推荐用兼容写法（会自动映射到运行时类）：

- Composite：`bt_add_node(graph_path, "Composite_Selector", pos_x, pos_y)`
- Task：`bt_add_node(graph_path, "Task_Wait", pos_x, pos_y)`

底层会构造：

- `BTComposite_Selector`
- `BTTask_Wait`

并在 C++ 侧通过 `UAIGraphNode::ClassData` + `PostPlacedNewNode()` 自动生成 `NodeInstance`。

### 5) 连接节点（父->子）

- `bt_connect_nodes(graph_path, parent_node_path, child_node_path)`

默认连接 parent 的第 0 个 output pin → child 的第 0 个 input pin。

推荐顺序：

- Root → Selector
- Selector → Wait

### 6) 绑定 Blackboard 并保存

- `bt_set_blackboard(bt_path, bb_path)`（C++ 侧直接写 `UBehaviorTree::BlackboardAsset`，避免 Python 侧 set_editor_property 受保护）
- 使用 UE Python `EditorAssetLibrary.save_asset` 保存 BT/BB（确保落盘）

## 已验证用例（2026-01-11 / UE 5.7 / LyraGame）

- 创建：
  - `/Game/VerifyMCP/BB_Auto_20260111_193606`
  - `/Game/VerifyMCP/BT_Auto_20260111_193606`
- Graph：
  - `...:Behavior Tree`
- 节点与连线：
  - Root → Selector → Wait
- Blackboard 绑定：
  - `BT.BlackboardAsset == BB`
- 保存成功（uasset 写入 Content/VerifyMCP）

## 常见坑

- **Python 侧 EdGraph.Nodes 读不到**：BehaviorTreeGraph 在 Python wrapper 中常被标记为 protected，必须走 C++。
- **Live Coding 新增 UFUNCTION**：运行中新增反射函数可能需要重启编辑器才能在 Python 侧看到；因此关键扩展通过“复用已有 UFUNCTION + op 多路复用”实现。

