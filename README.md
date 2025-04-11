# RemoteMCP 插件
这是一个基于UnrealEngine内置的Python插件实现的[MCP Server](https://modelcontextprotocol.io/introduction)。
该插件的目标是希望使得Unreal开发者可以更容易的利用AI来辅助Unreal项目的开发。


## 插件目标

在尝试 MCP 时，主要考虑以下场景：

1. **AI 提供思路参考**: 例如在判断报错信息时，通过 MCP 为 AI 提供上下文，帮助快速定位问题。
2. **批量任务处理**: 利用 AI 完成一次性的大量重复性工作，例如批量删除某类 Actor 或修改某类配置。
3. **自动化工作流**: 与其他自动任务工具（如 n8n）配合使用，使非程序背景的团队成员（如策划）也能定义自动化工作流。

## Quick Start
由于使用SSE的通信方式，所以该插件的使用非常的简单：
1. 将插件克隆到 Unreal Engine 的插件目录：
   ```bash
   git clone <repository-url> <Unreal-Engine-Plugins-Directory>/RemoteMCP
   ```
   
2. 启动引擎并在 `Edit->Plugins`面板中启动`RemoteMCP`插件

   ![image-20250410231644664](./Resources/plugin_image.png)

3. 重启引擎

此时MCP Server应当已经正常启动，你可以在`Edit -> EditorPreferences->MCP Setting`处检查MCP Server是否自动启动以及对应的Port

随后你可以使用任意的MCP Client来链接此MCP Server。 例如Cherry Studio，Cursor等。链接时选择使用SSE，并在链接中输入`http://localhost:<Your Port>/sse`即可。

如果你在设置中修改了Port，则可以在Unreal的Console中输入`MCP.Restart`来重新启动



## 工具扩展

目前该插件中只提供了少量的tool，目前核心功能都依赖AI通过编写python代码来实现。由于基于Unreal的Python

扩展来开发，所以新增tool也会非常方便。

当你需要扩展一个tool时，可以直接修改`Content\Python\tools\common_tools.py`，示例如下

``` python
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

# 许可证
此项目基于 MIT 许可证开源。详情请参阅 LICENSE 文件。


