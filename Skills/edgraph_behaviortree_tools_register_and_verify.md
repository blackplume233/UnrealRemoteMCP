# EdGraph / BehaviorTree Tools：注册与校验（RemoteMCP）

> AI(GPT-5.2) 记录：本文件用于沉淀“已验证有效”的注册与校验步骤，方便复现与排错。

## 背景

仓库内存在 `Content/Python/tools/edgraph_tools.py` 与 `Content/Python/tools/behaviortree_tools.py`，但默认注册链路只包含 common/resource/edit/livecoding/prompt，导致 `edgraph_*` / `bt_*` 工具在 MCP 中不可用。

另外，`FJsonObjectParameter`（Python 中的 `unreal.JsonObjectParameter`）在 Python 侧**无法直接调用** `JsonObjectFromString`（非 UFUNCTION），需要通过 `UMCPJsonUtils.MakeJsonObject()` 在 C++ 侧完成 JSON 解析，才能让 C++ 的 `Params->TryGet*Field(...)` 正常工作。

## 代码改动点

- **注册接入**：在 `Content/Python/tools/tool_register.py` 的 `register_all_tools()` 中新增：
  - `register_edgraph_tools(mcp)`
  - `register_behaviortree_tools(mcp)`

- **BehaviorTree 工具修复**（`Content/Python/tools/behaviortree_tools.py`）：
  - 去除重复定义的同名工具（避免注册覆盖/冲突）
  - `bt_add_node` 改为 `async def` 并 `await mcp.call_tool(...)`，避免返回 coroutine
  - 构造 C++ Json 参数改用 `unreal.MCPJsonUtils.make_json_object(json_str)`
  - 解析返回值改用 `unreal.MCPJsonUtils.json_object_to_string(res)`

## 运行时校验步骤（只读，不写入资产）

### 1) 热重载工具

在 UE 控制台执行：

- `mcp.reload`

### 2) 确认工具已注册（可选）

在 UE Python 执行（示例）：

```python
import foundation.global_context as gc
mcp = gc.get_mcp_instance()
names = [t.name for t in mcp._tool_manager.list_tools()]
print([n for n in names if n.startswith(("edgraph_", "bt_"))])
```

### 3) 调用“错误路径”用例，确认稳定返回 JSON（推荐）

- `edgraph_find_graphs_in_asset`（传不存在资产路径）应返回 `ok:false`
- `bt_get_graph`（传不存在 BT 路径）应返回 `success:false`
- `bt_get_auxiliary_nodes`（传不存在 node 路径）应返回 `success:false`

这些用例能验证：

- 工具确实可被调用（注册链路正确）
- 参数/返回值可序列化（MCP 不会因 coroutine/UE 对象导致 structuredContent 序列化失败）
- Json 参数解析链路正确（通过 `MCPJsonUtils`）

## 常见坑

- **只改了 `edgraph_tools.py/behaviortree_tools.py` 但没改注册**：工具不会出现在 MCP 列表里。
- **直接调用 `unreal.JsonObjectParameter().JsonObjectFromString`**：Python 侧不可用（非 UFUNCTION），会报类似 `AttributeError`。
- **同步 tool 里调用 `async def call_tool`**：会返回 coroutine，导致 MCP 无法返回预期结构。

