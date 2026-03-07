# RemoteMCP Plugin

该仓库包含 **RemoteMCP** 插件（Python 侧逻辑位于 `Content/Python`），用于把 Unreal Editor 的能力以 **MCP（Model Context Protocol）** 的方式暴露给外部客户端（例如 MCP Inspector / 自己写的 MCP Client）。

## Features

- **Game Thread Tools**：通过 `@mcp.game_thread_tool()` 把工具安全地派发到引擎 Tick/游戏线程执行
- **Console Command**：搜索并执行控制台命令
- **Actor / Blueprint / UMG 编辑能力**：读取 Actor 信息、生成/编辑蓝图、创建/操作 UMG（部分能力依赖插件内的 C++ Bridge）
- **EdGraph 通用工具（节点/连线 CRUD）**：对任意可拿到 `EdGraph` object path 的图，提供节点增删改查、pin 连接/断开、连线枚举（纯 Python + 反射兜底）
- **Domain Tools（按领域分组的工具）**：把大量工具按 `level/blueprint/umg/edgraph/behaviortree` 等 domain 分组，并为 domain 提供描述，便于 `get_dispatch` 发现与 `dispatch_tool` 调用
- **热重载**：支持在编辑器内重载 Python 工具定义

## Installation

1. 将插件放到 Unreal 工程的插件目录（示例）：

```bash
git clone <repository-url> <Unreal-Engine-Project>/Plugins/RemoteMCP
```

2. 在 Unreal Editor 中启用插件：
- **Edit -> Plugins**：启用 RemoteMCP（以及插件依赖项）
- **Edit -> Plugins -> Scripting**：启用 **Python Editor Script Plugin**
- 重启编辑器

> 可选：如需更新/补齐 Python 依赖，仓库提供了 `env.bat`（使用 `uv` 把依赖安装到 `Content/Python/Lib/site-packages`）。

## 正常使用流程（推荐）

### 1) 配置端口

RemoteMCP 的 Python 侧会读取 `unreal.MCPSetting.port` 作为服务端口（见 `init_mcp.py`）。请在 Unreal 的 **Project Settings** 中找到对应的 **MCPSetting**，设置 `Port`（例如 `8000`）。


### 2) 启动/停止/重载（在 Unreal 内触发）

插件通过桥接事件驱动服务生命周期：
- **START**：启动 MCP HTTP 服务（内部使用 Uvicorn + FastMCP Streamable HTTP）
- **RELOAD**：重载已注册的 Python tools
- **EXIT**：退出并清理桥接

本插件的 **C++ 层提供了控制台命令** 来触发这些事件（推荐用控制台命令来操作）：

- **`mcp.start`**：启动 MCP 服务
- **`mcp.stop`**：停止 MCP 服务
- **`mcp.restart`**：重启 MCP 服务（等价于 stop + start）
- **`mcp.reload`**：热重载 Python tools（不一定重启服务；主要用于你修改了 `tools/*` 后刷新工具列表）

> `mcp.reload` 的 Python 侧实现入口在 `tools/common_tools.py -> reload_all_tool()`，它内部会执行控制台命令 `mcp.reload`。

### 3) 客户端连接（MCP Inspector）

仓库提供 `inspector.bat` 一键启动 MCP Inspector：

```bash
inspector.bat
```

在 Inspector 中选择 **Streamable HTTP**，填入服务地址：
- `http://127.0.0.1:<port>/mcp`
- 如果从其他机器连接，把 `127.0.0.1` 换成运行 Unreal 的那台机器 IP
``` json
    "unreal_mcp": {
      "type": "streamable-http",
      "url": "http://localhost:<port>/mcp",
      "note": "For Streamable HTTP connections, add this URL directly in your MCP Client"
    }
```

### 3.5) 客户端连接（Cursor）

Cursor 支持通过 **URL** 直连 MCP Server（无需 `command/args` 启动本地进程）。推荐把配置写到 **项目级** 的 `.cursor/mcp.json`，这样团队协作更一致。

#### A) 写入项目级配置（推荐）

在你的 Unreal 工程（或你当前工作区）根目录创建文件：`.cursor/mcp.json`，内容示例：

```json
{
  "mcpServers": {
    "unreal_mcp": {
      "url": "http://127.0.0.1:8422/mcp"
    }
  }
}
```

把 `8422` 替换成你在 Unreal **Project Settings -> MCPSetting -> Port** 配置的端口。

#### B) 写入全局配置（可选）

如果希望所有工程都能看到该 MCP Server，可以把同样的 JSON 写到：
- Windows：`%USERPROFILE%\\.cursor\\mcp.json`
- macOS/Linux：`~/.cursor/mcp.json`

#### C) 在 Cursor 里启用并验证

- 在 Unreal 里先启动服务：控制台执行 `mcp.start`（或 `mcp.restart`）
- 在 Cursor 打开 **Settings -> MCP**（或设置里搜索 “MCP”），你会看到 `unreal_mcp`
- 启用后应出现绿色状态点，并能看到工具列表（例如 `test_engine_state`）

#### D) 常见问题（Cursor 侧）

- **一直连接不上**：确认 URL 包含 `/mcp`，例如 `http://127.0.0.1:9527/mcp`
- **远程连接失败**：把 `127.0.0.1` 换成运行 Unreal 的机器 IP，并放行该端口的防火墙入站规则
- **工具列表不刷新**：在 Unreal 控制台执行 `mcp.reload`（必要时 `mcp.restart`），然后在 Cursor 的 MCP 面板里重新连接/刷新

### 4) 验证连接（建议先跑这几个工具）

连接成功后，优先调用：
- `test_engine_state`：返回引擎/端口/Python 信息，确认链路可用
- `test_tool`：最小回显测试
- `run_python_script`：在编辑器内执行 Python 片段（推荐把输出写到变量 `result`）

`run_python_script` 示例：

```python
# 作为 tool 参数传入的 script 字符串内容
import unreal
result = {
  "level": unreal.EditorLevelLibrary.get_current_level_name(),
  "actor_count": len(unreal.EditorLevelLibrary.get_all_level_actors())
}
```

## EdGraph 通用 CRUD（最小示例）

> 说明：默认**不保存资产**。需要写回磁盘请在写操作里传 `auto_save_asset_path="/Game/..."`。

1) 发现资产里的图（以 Blueprint 为例；其他资产会做“反射式”尽力扫描）：

```python
result = unreal.MCPPythonBridge.call_tool("edgraph_find_graphs_in_asset", {"asset_path": "/Game/BP_MyActor.BP_MyActor"})
```

2) 列出节点：

```python
result = unreal.MCPPythonBridge.call_tool("edgraph_list_nodes", {"graph_path": "/Game/BP_MyActor.BP_MyActor:EventGraph"})
```

3) 添加一个注释节点（`EdGraphNode_Comment`）：

```python
result = unreal.MCPPythonBridge.call_tool("edgraph_add_node", {
  "graph_path": "/Game/BP_MyActor.BP_MyActor:EventGraph",
  "node_class": "EdGraphNode_Comment",
  "pos_x": 0,
  "pos_y": 0,
  "properties": {"node_comment": "Hello EdGraph"},
  "auto_save_asset_path": "/Game/BP_MyActor.BP_MyActor"
})
```

## Domain Tools 文档

- 说明与回归测试步骤见：`docs/domain_tools.md`


## 使用参考
考虑使用Cursor打开任意一个空目录，拷贝CLAUDE.md进该目录。
在Cursor中配置mcp.json，例如：
``` cursor setting -> Tools & MCP -> Add Custom MCP ```
``` json
{
    "unreal_mcp": {
        "type": "streamable-http",
        "url": "http://localhost:<port>/mcp",
        "note": "For Streamable HTTP connections, add this URL directly in your MCP Client"
    }
}
```
并在``` cursor setting -> Tools & MCP -> Rule and Commands  ```中勾选 ```include CLAUDE.md in Context```


## 常见问题排查

### 端口无法访问

- Unreal 侧服务默认绑定在 `127.0.0.1`（仅本机访问）；如需远程连接，请在 `MCPSetting` 中配置 host 为 `0.0.0.0` 并放行防火墙端口
- 确认 Inspector 连接的是 `http://<ip>:<port>/mcp`（注意包含 `/mcp` 路径）

### 修改了 tools 但客户端没看到更新

- 在 Unreal 控制台执行：`mcp.reload`
- 如果你同时改了桥接/服务相关逻辑，或遇到状态异常，直接用：`mcp.restart`
- 或者在客户端调用 tool：`reload_all_tool`
