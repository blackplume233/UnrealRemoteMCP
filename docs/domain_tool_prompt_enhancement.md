# Domain Tool Prompt 增强建议

> AI(Claude Opus 4.5): 用于改进 AI 对 Domain Tool 系统使用效果的 Prompt 增强文档

## 问题分析

当前 AI 无法有效使用 domain tools 的原因：

1. **默认 prompt 中没有提及 domain tools**
2. **AI 不知道什么场景下应该使用哪个 domain**
3. **两步调用流程增加认知负担**

## 建议添加到 `prompt.py` 的内容

在 `default_prompt` 中的 `## MCP 常用能力速查` 部分后添加：

```python
### Domain Tools（专业领域工具）

Domain Tools 是按领域分组的专业工具，用于特定场景的深度操作。

**发现和使用流程：**
1. `get_dispatch()` - 列出所有可用的 domain
2. `get_dispatch(domain="xxx")` - 获取该 domain 下的工具列表和参数
3. `dispatch_tool(domain, tool_name, arguments_json)` - 执行具体工具

**或者使用搜索：**
- `search_domain_tools(keyword)` - 按关键词搜索 domain 工具

**已注册的 Domain：**

| Domain | 使用场景 | 核心工具 |
|--------|----------|----------|
| `edgraph` | 操作任意 EdGraph（蓝图节点图、材质图等）的底层节点/连线 | `edgraph_list_nodes`, `edgraph_add_node`, `edgraph_connect_pins` |
| `behaviortree` | 创建/编辑行为树资产 | `bt_create_asset`, `bt_add_node`, `bt_connect_nodes` |

**何时使用 Domain Tools：**
- 需要编辑**行为树 (Behavior Tree)** → 使用 `behaviortree` domain
- 需要底层操作**蓝图节点图/材质图的节点和连线** → 使用 `edgraph` domain
- 普通蓝图组件/属性设置 → 优先用现有的 `create_blueprint`、`add_component_to_blueprint` 等直接工具

**调用示例（创建行为树并添加节点）：**
```
1. get_dispatch(domain="behaviortree")  # 查看可用工具
2. dispatch_tool(domain="behaviortree", tool_name="bt_create_asset", 
                arguments='{"name": "MyBT", "package_path": "/Game/AI"}')
3. dispatch_tool(domain="behaviortree", tool_name="bt_add_node",
                arguments='{"graph_path": "...", "node_class": "BTComposite_Selector"}')
```
```

## 场景-工具映射表（建议加入 Prompt）

```markdown
### 场景速查：何时用什么工具？

| 我想做... | 推荐工具 |
|-----------|----------|
| 创建/修改 Actor | `spawn_actor`, `set_actor_property`, `set_actor_transform` |
| 创建/修改 Blueprint 组件 | `create_blueprint`, `add_component_to_blueprint` |
| 蓝图事件图搭建 | `add_blueprint_event_node`, `add_blueprint_function_node`, `connect_blueprint_nodes` |
| 创建 UMG Widget | `create_umg_widget_blueprint`, `add_button_to_widget` |
| **创建/编辑行为树** | `get_dispatch("behaviortree")` → `bt_*` 系列工具 |
| **底层 EdGraph 节点操作** | `get_dispatch("edgraph")` → `edgraph_*` 系列工具 |
| 复杂脚本/批量操作 | `run_python_script` |
```

## 可选代码改进：直接暴露高频 Domain Tools

如果希望 AI 能直接调用 `bt_*` 和 `edgraph_*` 工具而不需要 dispatch 流程，可以修改 `mcp_app.py` 中的 `domain_tool` 装饰器，增加一个 `also_expose` 参数：

```python
def domain_tool(
    self, 
    domain: str, 
    name: str | None = None, 
    description: str | None = None,
    game_thread: bool = True,
    also_expose: bool = False  # 新增：是否同时注册为普通 tool
) -> Callable[[AnyFunction], AnyFunction]:
    """..."""
    def decorator(fn: AnyFunction) -> AnyFunction:
        func_name = name or fn.__name__
        fn_desc = description or fn.__doc__ or ""
        
        # 注册到 domain tools
        if domain not in self._domain_tools:
            self._domain_tools[domain] = {}
        tool = Tool.from_function(fn, name=func_name, description=fn_desc)
        self._domain_tools[domain][func_name] = tool
        
        # 可选：同时注册为普通 tool
        if also_expose:
            self.add_tool(fn, func_name, f"[{domain}] {fn_desc}")
        
        if game_thread:
            full_key = f"{domain}:{func_name}"
            self._domain_game_thread_tools.add(full_key)
        
        unreal.log(f"[DomainTool] Registered: {domain}/{func_name}")
        return fn
    return decorator
```

然后在 `behaviortree_tools.py` 和 `edgraph_tools.py` 中，对高频工具加上 `also_expose=True`：

```python
@mcp.domain_tool("behaviortree", also_expose=True)
def bt_create_asset(name: str, package_path: str = "/Game/"):
    ...
```

这样 AI 可以：
- 直接调用 `bt_create_asset()` （无需 dispatch 流程）
- 或者通过 `dispatch_tool()` 调用（保持兼容）

## 实施建议

1. **立即可做**：将上述内容添加到 `prompt.py` 的 `default_prompt` 中
2. **可选改进**：实现 `also_expose` 功能，让高频 domain tools 直接可用
3. **长期优化**：收集 AI 使用 domain tools 的成功/失败案例，持续改进 prompt
