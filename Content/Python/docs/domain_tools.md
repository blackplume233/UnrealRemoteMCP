# Domain Tools（按领域分组的工具）说明与验证记录

本项目在 `UnrealMCP` 中实现了 **Domain Tool 系统**：工具按领域（domain）分组，不进入默认 tools 列表；需要通过 `get_dispatch` / `dispatch_tool` 使用。

## 1. 为什么要用 Domain Tools

- 减少默认工具列表噪音，让客户端/Agent **先按领域发现工具**，再精确调用
- 可以给每个 domain 添加 **description**，提升“工具发现”体验

## 2. 如何发现与调用

### 2.1 列出所有 Domain（含描述）

调用：
- `get_dispatch(domain="")`

预期关键字段：
- `domains`: domain 名称列表
- `domains_info`: domain + description 列表

### 2.2 获取某个 Domain 内的工具列表（含参数 schema）

调用：
- `get_dispatch(domain="level")`
- `get_dispatch(domain="edgraph")`
- `get_dispatch(domain="behaviortree")`

预期关键字段：
- `domain`: 当前 domain
- `description`: 当前 domain 的说明
- `tools`: 工具列表（每个工具含 name/description/parameters）

### 2.3 调用 Domain Tool

调用：
- `dispatch_tool(domain="level", tool_name="get_actors_in_level", arguments="{}")`

说明：
- `arguments` 必须是 JSON 字符串，例如 `'{"name":"Foo"}'`

## 3. 当前已注册 Domain（说明来源）

- `level` / `blueprint` / `umg`：在 `tools/edit_tools.py -> register_edit_tool()` 内通过 `mcp.set_domain_description()` 设置
- `edgraph`：在 `tools/edgraph_tools.py -> register_edgraph_tools()` 内设置
- `behaviortree`：在 `tools/behaviortree_tools.py -> register_behaviortree_tools()` 内设置

## 4. MCP 实测输出（2026-01-27，UE 5.7，端口 8422）

### 4.1 `get_dispatch()`（节选）

```json
{
  "domains": ["level", "blueprint", "umg", "edgraph", "behaviortree"],
  "domains_info": [
    {"domain":"level","description":"关卡/Actor/视口相关编辑器能力：查询 Actor、生成/删除 Actor、设置 Transform/属性、视口聚焦等。"},
    {"domain":"blueprint","description":"蓝图资产与蓝图图编辑：创建/编译蓝图、添加组件、设置组件/蓝图属性、在蓝图图里添加/连接节点等。"},
    {"domain":"umg","description":"UMG Widget 蓝图与界面绑定：创建 Widget、添加控件、绑定事件、添加到视口等。"},
    {"domain":"edgraph","description":"通用 EdGraph 底层操作：发现图、节点增删改查、pin 连线枚举/连接/断开。可复用于蓝图图、行为树图等编辑器图。"},
    {"domain":"behaviortree","description":"行为树（Behavior Tree）资产编辑与节点操作：创建行为树/黑板、获取图、添加/连接节点、设置黑板与常见任务参数等。"}
  ]
}
```

### 4.2 `search_domain_tools(keyword="spawn_actor")`（节选）

预期：能在 `level` domain 下命中 `spawn_actor`，并返回参数 schema。

```json
{
  "keyword": "spawn_actor",
  "matches": [
    {
      "domain": "level",
      "name": "spawn_actor"
    }
  ],
  "total_count": 1
}
```

### 4.3 `dispatch_tool(domain="level", tool_name="get_actors_in_level")`

预期：返回当前关卡 Actor 列表（每项包含 name/path/class/transform）。

## 5. 回归测试步骤（推荐）

1) 执行 `mcp.reload`
2) 调用 `get_dispatch(domain="")`，确认 `domains_info[*].description` 非空
3) 调用 `dispatch_tool(domain="level", tool_name="get_actors_in_level", arguments="{}")`，确认返回非空列表

