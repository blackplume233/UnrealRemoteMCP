# RemoteMCP 插件

> [!NOTE]
> 本项目用于开发 UnrealMCP。

这是一个基于UnrealEngine内置的Python插件实现的[MCP Server](https://modelcontextprotocol.io/introduction)。
该插件的目标是希望使得Unreal开发者可以更容易的利用AI来辅助Unreal项目的开发。

## 插件目标

在尝试 MCP 时，主要考虑以下场景：

1. **AI 提供思路参考**: 例如在判断报错信息时，通过 MCP 为 AI 提供上下文，帮助快速定位问题。
2. **批量任务处理**: 利用 AI 完成一次性的大量重复性工作，例如批量删除某类 Actor 或修改某类配置。
3. **自动化工作流**: 与其他自动任务工具（如 n8n）配合使用，使非程序背景的团队成员（如策划）也能定义自动化工作流。

## Quick Start

> 现在是AI的时代了，当你下载完本仓库之后可以直接咨询AI这个工具应该如何使用，AI应该会给到更真实，符合最新版本的使用指导

该插件会在 Unreal Editor 内启动一个 **MCP Server（Streamable HTTP）**，使用非常简单：

1. 将插件克隆到 Unreal Engine 的插件目录：

   ```bash
   git clone <repository-url> <Unreal-Engine-Plugins-Directory>/RemoteMCP
   ```
2. 安装python依赖，首先保证本地有uv或者pip,最好是使用uv，保证python版本为3.11，然后使用pip下载以下几个package到指定目录

   ```
   cd <Repo>/Content/Python
   uv pip install httpx --target ./Lib/site-packages --force-reinstall --upgrade
   uv pip install mcp[cli] --target ./Lib/site-packages --force-reinstall --upgrade
   uv pip install anyio --target ./Lib/site-packages --force-reinstall --upgrade   
   uv pip install pywin32 --target ./Lib/site-packages --force-reinstall --upgrade

   ```
3. 启动引擎并在 `Edit->Plugins`面板中启动 `RemoteMCP`插件
4. 重启引擎
5. 设置 `Edit -> Editor Preferences -> MCP Setting->Enable` 为True，（同时建议打开AutoStart),重启引擎
6. 使用控制台命令 mcp.start，如果你启用了AutoStart则不需要这一步

此时MCP Server应当已经正常启动，你可以在 `Edit -> EditorPreferences->MCP Setting`处检查MCP Server是否自动启动以及对应的Port

随后你可以使用任意的 MCP Client 来连接该 MCP Server（例如 Cherry Studio、Cursor 等）。连接时选择 **Streamable HTTP**，并在链接中输入 `http://localhost:<Your Port>/mcp` 即可。

如果你在设置中修改了Port，则可以在Unreal的Console中输入 `MCP.Restart`来重新启动

## 使用参考（零基础也能上手）

下面按“完全没经验的小白”视角，从 0 开始把 UE 侧、Cursor 侧、验证与排错全部走通。

### 0）你需要准备什么

- **Unreal Editor**：需要在编辑器里运行（不是打包后的游戏）。
- **插件**：启用 `RemoteMCP`，并同时启用 Unreal 自带的 **Python Editor Script Plugin**（`Edit -> Plugins -> Scripting`）。
- **重启编辑器**：启用插件后必须重启一次。

### 1）在 Unreal 里确认端口（一定要先做）

1. 打开 `Edit -> Editor Preferences -> MCP Setting`
2. 找到 `Port`（例如 `8422`），记下来
3. 如你修改过端口，后面客户端 URL 里的端口也要跟着改

> 小提示：服务默认 URL 形如 `http://127.0.0.1:<port>/mcp`（注意必须带 `/mcp` 路径）。

### 2）启动 / 停止 / 重载（在 Unreal 控制台执行）

在 Unreal 的输出日志（Output Log）里打开控制台输入框，执行以下命令：

- **启动**：`MCP.Start`
- **停止**：`MCP.Stop`
- **重启（推荐）**：`MCP.Restart`
- **热重载工具列表**（你改了 `Content/Python/tools/*` 但客户端看不到更新时用）：`MCP.Reload`
- **查看状态**：`MCP.State`

### 3）用 Cursor 连接（推荐：最适合新手）

#### A）准备一个“AI 工作区”（强烈推荐）

1. 在任意位置新建一个空文件夹（例如 `D:\UnrealAIWorkspace`），用 Cursor 打开它
2. 把本仓库里的 `CLAUDE.md` **复制**到这个空文件夹根目录
3. 在 Cursor 设置里：`Tools & MCP -> Rule and Commands` 勾选 **include `CLAUDE.md` in Context**

#### B）配置 Cursor 的 MCP（项目级配置：最稳）

在你刚才的“AI 工作区”根目录创建文件：`.cursor/mcp.json`，内容如下（把 `<port>` 改成你在 UE 里看到的端口）：

```json
{
  "mcpServers": {
    "unreal_mcp": {
        "type": "streamable-http",
        "url": "http://127.0.0.1:<port>/mcp"
    }
  }
}
```

> 说明：`127.0.0.1` 表示 Unreal 跑在你本机；如果 Unreal 在另一台机器上，把它改成那台机器的局域网 IP（并放行防火墙端口）。

#### C）在 Cursor 里启用并验证

1. 先回到 Unreal 执行一次 `MCP.Restart`
2. 在 Cursor 打开 `Settings -> Tools & MCP`（或设置里搜索 “MCP”）
3. 找到 `unreal_mcp` 并连接/启用
4. 连接成功后你应该能看到工具列表（例如 `get_unreal_state`、`run_python_script`）

### 4）用其他 MCP Client 连接（Cherry Studio / Inspector 等）

- **连接类型**：选择 **Streamable HTTP**
- **URL**：`http://127.0.0.1:<port>/mcp`

### 5）新手必做：用 2 个最简单的工具验证链路

连接成功后，建议立刻调用：

- **`get_unreal_state`**：确认引擎在跑、端口配置正确、当前关卡/Actor 数量可读
- **`run_python_script`**：跑一段最小脚本（建议把输出写到 `result` 变量）

`run_python_script` 示例：

```python
import unreal
result = {
    "level": unreal.EditorLevelLibrary.get_current_level_name(),
    "actor_count": len(unreal.EditorLevelLibrary.get_all_level_actors())
}
```

### 6）常见问题（90% 的“连不上/没反应”都在这）

- **一直连接不上**：检查 URL 是否包含 `/mcp`，例如 `http://127.0.0.1:8422/mcp`
- **改了端口但还是旧端口**：UE 里改完 `Port` 后执行 `MCP.Restart`
- **工具列表不刷新**：UE 控制台执行 `MCP.Reload`（不行就 `MCP.Restart`），然后在客户端刷新/重连
- **远程连接失败**：把 `127.0.0.1` 换成运行 Unreal 的机器 IP，并放行该端口的防火墙入站规则

## 工具扩展

目前该插件中只提供了少量的tool，目前核心功能都依赖AI通过编写python代码来实现。由于基于Unreal的Python

扩展来开发，所以新增tool也会非常方便。

当你需要扩展一个tool时，可以直接修改 `Content\Python\tools\common_tools.py`，示例如下

```python
def register_common_tools(mcp : UnrealMCP):
    @mcp.tool()
    def first_tool():
        return "Hello from first tool!"
  
    @mcp.game_thread_tool()
    def get_actor_count():
        """Get the number of actors in the current Unreal Engine scene."""
        try:
            # 使用 Unreal 的 ActorIterator 获取所有 Actor
            world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            if not world:
                unreal.log_error("Failed to get the current world.")
                return 0
            actor_count = sum(1 for _ in unreal.ActorIterator(world))
            unreal.log(f"Number of actors in the scene: {actor_count}")
            return actor_count
        except Exception as e:
            unreal.log_error(f"Failed to get actor count: {str(e)}")
            return 0
```

# 项目结构

```
RemoteMCP
├── Content
│   ├── EditorUI
│   │   └── MainPanel.uasset
│   └── Python
│       ├── foundation
│       │   ├── global_context.py
│       │   ├── log_handler.py
│       │   ├── mcp_app.py
│       │   └── utility.py
│       ├── tools
│       │   └── common_tools.py
│       ├── env.bat
│       ├── init_mcp.py
│       ├── inspector.bat
│       └── unreal_python_tools.py
├── Resources
│   └── plugin_image.png
├── Source
│   └── RemoteMCP
│       ├── Private
│       │   └── RemoteMCP.cpp
│       └── Public
│           ├── RemoteMCP.h
│           └── Settings.h
├── PromptCase.md
├── README.md
└── RemoteMCP.uplugin
```

# 许可证

此项目基于 MIT 许可证开源。详情请参阅 LICENSE 文件。
