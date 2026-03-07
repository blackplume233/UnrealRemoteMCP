# Domain Tool 系统使用指南

> AI(Claude Opus 4.5): Domain Tool 系统文档

## 概述

Domain Tool 系统允许将工具按领域（domain）分组，这些工具不会出现在默认的 MCP tools 列表中，而是通过 `get_dispatch` 和 `dispatch_tool` 两个接口来访问和调用。

**优势：**
- 减少默认工具列表的噪音
- 让 AI 按需获取特定领域的工具
- 更好的工具组织和发现机制

## 已注册的 Domain

| Domain | 描述 | 工具数量 |
|--------|------|---------|
| `edgraph` | EdGraph 节点/连线的增删改查 | 9 个工具 |
| `behaviortree` | 行为树资产编辑工具 | 10 个工具 |

## 注册 Domain Tool

在工具模块中使用 `@mcp.domain_tool()` 装饰器注册：

```python
def register_my_domain_tools(mcp: UnrealMCP):
    
    @mcp.domain_tool("animation")
    def play_animation(actor_name: str, anim_name: str):
        """播放指定 Actor 的动画
        
        Args:
            actor_name: Actor 名称
            anim_name: 动画资产名称
        """
        # 实现...
        return {"success": True}
    
    @mcp.domain_tool("animation", name="stop_anim", description="停止动画播放")
    def stop_animation(actor_name: str):
        # 实现...
        pass
    
    # 如果工具不需要在 game thread 执行，可以设置 game_thread=False
    @mcp.domain_tool("utility", game_thread=False)
    def calculate_something(value: int) -> int:
        return value * 2
```

### 装饰器参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `domain` | str | (必填) | 工具所属领域名称 |
| `name` | str | 函数名 | 工具名称 |
| `description` | str | docstring | 工具描述 |
| `game_thread` | bool | True | 是否在 UE 主线程执行 |

## AI 调用流程

### 1. 发现可用领域

```
调用: get_dispatch()
返回: {"domains": ["animation", "material", "landscape"], "hint": "..."}
```

### 2. 获取领域工具信息

```
调用: get_dispatch(domain="animation")
返回: {
    "domain": "animation",
    "tools": [
        {
            "name": "play_animation",
            "description": "播放指定 Actor 的动画",
            "parameters": {
                "type": "object",
                "properties": {
                    "actor_name": {"type": "string"},
                    "anim_name": {"type": "string"}
                },
                "required": ["actor_name", "anim_name"]
            }
        },
        ...
    ]
}
```

### 3. 调用工具

```
调用: dispatch_tool(
    domain="animation", 
    tool_name="play_animation", 
    arguments='{"actor_name": "MyCharacter", "anim_name": "Walk"}'
)
返回: 工具执行结果
```

## 完整示例

### 注册示例（material_tools.py）

```python
from foundation.mcp_app import UnrealMCP
import unreal

def register_material_tools(mcp: UnrealMCP):
    
    @mcp.domain_tool("material")
    def get_material_parameters(material_path: str) -> dict:
        """获取材质的所有参数
        
        Args:
            material_path: 材质资产路径，如 /Game/Materials/M_Example
        """
        mat = unreal.EditorAssetLibrary.load_asset(material_path)
        if not mat:
            return {"error": f"Material not found: {material_path}"}
        
        # 获取参数...
        return {"parameters": [...]}
    
    @mcp.domain_tool("material")
    def set_scalar_parameter(material_path: str, param_name: str, value: float):
        """设置材质的标量参数
        
        Args:
            material_path: 材质资产路径
            param_name: 参数名称
            value: 参数值
        """
        # 实现...
        return {"success": True}
```

### 在 tool_register.py 中注册

```python
import tools.material_tools as material_register

def register_all_tools(mcp: FastMCP):
    # ... 其他注册 ...
    material_register.register_material_tools(mcp)
```

## 注意事项

1. **默认在 game thread 执行**：大多数 UE 操作需要在主线程执行，所以 `game_thread` 默认为 True
2. **JSON 参数**：`dispatch_tool` 的 `arguments` 参数需要是有效的 JSON 字符串
3. **错误处理**：如果 domain 或 tool_name 不存在，会返回包含错误信息的 `CallToolResult`
4. **热重载支持**：domain tools 会随 `reload_all_tool` 一起重新注册

---

## 内置 Domain 工具参考

### Domain: `edgraph`

EdGraph 节点/连线的增删改查工具。

| 工具名 | 描述 |
|--------|------|
| `edgraph_find_graphs_in_asset` | 在指定资产里发现 EdGraph |
| `edgraph_list_nodes` | 列出图内所有节点 |
| `edgraph_get_node` | 按 guid/name/path 查询单个节点 |
| `edgraph_add_node` | 在图内创建一个 EdGraphNode |
| `edgraph_delete_node` | 从图内删除节点 |
| `edgraph_set_node_properties` | 修改节点属性 |
| `edgraph_list_links` | 枚举图里所有 pin 连接 |
| `edgraph_connect_pins` | 连接两个 pin |
| `edgraph_disconnect_pin` | 断开指定 pin 的所有连接 |

### Domain: `behaviortree`

行为树 (Behavior Tree) 专用编辑工具。

| 工具名 | 描述 |
|--------|------|
| `bt_get_graph` | 获取行为树资产内部的 Graph 对象路径 |
| `bt_set_blackboard` | 设置 BehaviorTree 的 BlackboardAsset |
| `bt_set_wait_time` | 设置 BTTask_Wait 的 WaitTime |
| `bt_create_asset` | 创建新的行为树资产 |
| `bt_create_blackboard` | 创建新的黑板资产 |
| `bt_get_auxiliary_nodes` | 获取 BT 节点上挂载的辅助节点 |
| `bt_list_graph_nodes` | 列出行为树 Graph 内所有节点 |
| `bt_connect_nodes` | 连接行为树节点（父->子） |
| `bt_add_node` | 向行为树添加节点（Task/Composite） |
