"""
slate_tools.py
通过 MCP 操作 Unreal Editor Slate UI 的工具集。

功能分类：
  查询类（只读）：
    - slate_get_all_windows          列出所有顶层窗口
    - slate_get_widget_tree          获取窗口 Widget 树
    - slate_get_widget_under_cursor  获取当前鼠标下的 Widget 路径
    - slate_get_widget_at_position   获取指定屏幕坐标处的 Widget 路径
    - slate_find_widgets_by_type     按 Widget 类型名搜索
    - slate_get_all_text_blocks      收集界面所有非空文本
    - slate_get_editor_ui_summary    UI 全貌摘要
    - slate_get_active_window        获取当前激活窗口信息
    - slate_get_focused_widget       获取当前键盘焦点 Widget
    - slate_get_all_dock_tabs        列出所有打开的 DockTab

  窗口管理：
    - slate_move_window              移动窗口到指定屏幕位置
    - slate_resize_window            调整窗口大小
    - slate_close_window             关闭/销毁窗口
    - slate_close_dock_tab           关闭指定 DockTab（Project Settings/Plugins 等）
    - slate_safe_close               安全关闭（优先 DockTab，必要时才关窗口）

  焦点管理：
    - slate_set_keyboard_focus       将键盘焦点设置到指定坐标处的 Widget

  Tab / 面板：
    - slate_invoke_tab               通过 Tab ID 打开或切换到 Editor 面板

  交互类（写入/模拟输入）：
    - slate_click_at_position        模拟鼠标点击（屏幕坐标）
    - slate_send_text_input          向焦点控件发送文本输入
    - slate_send_key_press           发送键盘按键（含组合键）
    - slate_scroll_at_position       模拟鼠标滚轮滚动

  通知：
    - slate_show_notification        在编辑器右下角弹出通知气泡

所有交互工具均在游戏主线程（game_thread_tool）执行，以确保 Slate 线程安全。
"""

from typing import Any, Dict, List, Optional
from foundation.mcp_app import UnrealMCP
from foundation.utility import call_cpp_tools
import unreal


def register_slate_tools(mcp: UnrealMCP):
    """向 MCP 服务器注册所有 Slate UI 工具。"""

    mcp.set_domain_description(
        "slate",
        (
            "Slate UI 全套操作能力，包括：\n"
            "查询 - 遍历 Widget 树、获取窗口/焦点/Tab 列表；\n"
            "窗口管理 - 移动/调整/关闭顶层窗口；\n"
            "Tab 管理 - 通过 ID 打开编辑器面板（OutputLog/ContentBrowser1/WorldOutliner 等）；\n"
            "交互 - 鼠标点击、滚轮滚动、键盘输入、设置键盘焦点；\n"
            "通知 - 在编辑器右下角弹出状态通知气泡。"
        ),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 查询工具（只读，domain_tool 按需激活）
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_all_windows() -> List[Dict[str, Any]]:
        """
        获取 Unreal Editor 当前所有顶层窗口的基本信息。

        Returns:
            list of dict，每项包含：
              index       - 窗口索引（用于其他工具的 window_index 参数）
              title       - 窗口标题
              window_type - 窗口类型（Normal/Menu/ToolTip/Notification 等）
              is_visible  - 是否可见
              is_active   - 是否激活
              is_focused  - 是否是当前焦点顶层窗口
              position    - {x, y} 屏幕位置（像素）
              size        - {width, height} 窗口大小（像素）
        """
        result = call_cpp_tools(unreal.MCPSlateTools.handle_get_all_windows, {})
        return result.get("windows", [])

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_widget_tree(
        window_index: int = -1,
        window_title: str = "",
        max_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        获取指定窗口的 Slate Widget 树结构（JSON 嵌套格式）。

        Args:
            window_index: 窗口索引（来自 slate_get_all_windows），-1 表示自动选择
            window_title: 按标题匹配窗口（模糊匹配，优先级低于 window_index）
            max_depth:    遍历深度上限（1~12），默认 5；越深结果越大

        Returns:
            dict:
              window_title - 目标窗口标题
              max_depth    - 实际使用的深度
              widget_tree  - 嵌套 Widget 结构，每节点包含 type/tag/visibility/children
        """
        params: Dict[str, Any] = {"max_depth": max_depth}
        if window_index >= 0:
            params["window_index"] = window_index
        if window_title:
            params["window_title"] = window_title
        return call_cpp_tools(unreal.MCPSlateTools.handle_get_widget_tree, params)

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_widget_under_cursor() -> Dict[str, Any]:
        """
        获取当前鼠标光标所在位置的 Widget 路径及几何信息。

        Returns:
            dict:
              found         - 是否找到 Widget
              cursor_x/y    - 光标屏幕坐标
              window_title  - 所属窗口标题
              leaf_widget_type - 最顶层（末尾）Widget 类型名
              widget_path   - 从窗口根到末尾 Widget 的路径数组，每项含:
                              type / tag / text(部分) / geometry{x,y,width,height}
        """
        return call_cpp_tools(unreal.MCPSlateTools.handle_get_widget_under_cursor, {})

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_widget_at_position(x: float, y: float) -> Dict[str, Any]:
        """
        获取指定屏幕坐标（像素）处的 Widget 路径，不移动实际鼠标光标。

        Args:
            x: 屏幕 X 坐标（像素，相对于屏幕左上角）
            y: 屏幕 Y 坐标（像素）

        Returns:
            同 slate_get_widget_under_cursor 格式，query_x/query_y 替代 cursor_x/y
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_get_widget_at_position,
            {"x": x, "y": y},
        )

    @mcp.domain_tool("slate", game_thread=True)
    def slate_find_widgets_by_type(
        type_name: str,
        window_index: int = -1,
        window_title: str = "",
        max_depth: int = 8,
    ) -> Dict[str, Any]:
        """
        在 Slate Widget 树中按类型名称搜索匹配的 Widget。

        常用类型名举例：
          STextBlock, SButton, SEditableText, SEditableTextBox,
          SCheckBox, SComboBox, SListView, SScrollBox, SDockTab,
          SWindow, SBorder, SImage, SSplitter, SSearchBox

        Args:
            type_name:    要搜索的 Widget 类型名（大小写敏感）
            window_index: 限定搜索窗口（-1 表示搜索所有窗口）
            window_title: 按标题限定窗口（优先级低于 window_index）
            max_depth:    搜索深度上限（默认 8）

        Returns:
            dict:
              searched_type - 查询的类型名
              count         - 找到的数量
              widgets       - 列表，每项含 type/tag/text/depth/in_window/visibility
        """
        params: Dict[str, Any] = {
            "type_name": type_name,
            "max_depth": max_depth,
        }
        if window_index >= 0:
            params["window_index"] = window_index
        if window_title:
            params["window_title"] = window_title
        return call_cpp_tools(unreal.MCPSlateTools.handle_find_widgets_by_type, params)

    # ─────────────────────────────────────────────────────────────────────────
    # 交互工具（写入，game_thread_tool 确保主线程安全）
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.game_thread_tool()
    def slate_click_at_position(x: float, y: float, button: str = "Left") -> Dict[str, Any]:
        """
        在指定屏幕坐标（像素）模拟鼠标按下+抬起（单击）。

        注意：坐标基于全屏幕像素，可通过 slate_get_widget_tree 中的 geometry
        或 slate_get_widget_at_position 获取目标位置。

        Args:
            x:      屏幕 X 坐标（像素）
            y:      屏幕 Y 坐标（像素）
            button: 鼠标按键，"Left"（默认）/ "Right" / "Middle"

        Returns:
            dict:
              success            - 是否成功找到目标 Widget 并发送事件
              x, y               - 实际点击的坐标
              button             - 使用的按键
              clicked_widget_type - 被点击的 Widget 类型名
              clicked_widget_tag  - 被点击的 Widget tag（如有）
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_click_at_position,
            {"x": x, "y": y, "button": button},
        )

    @mcp.game_thread_tool()
    def slate_send_text_input(text: str) -> Dict[str, Any]:
        """
        向当前键盘焦点控件逐字符发送文本输入（模拟用户打字）。

        适合场景：在 slate_click_at_position 点击文本框后，再调用此工具输入内容。

        Args:
            text: 要输入的字符串（支持任意 Unicode 字符）

        Returns:
            dict:
              success    - 是否执行
              text       - 实际发送的文本
              char_count - 发送的字符数量
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_send_text_input,
            {"text": text},
        )

    @mcp.game_thread_tool()
    def slate_send_key_press(
        key: str,
        shift: bool = False,
        ctrl: bool = False,
        alt: bool = False,
        text: str = "",
    ) -> Dict[str, Any]:
        """
        向当前焦点控件发送键盘按键事件。

        常用 key 名称（与 UE FKey 名称一致）：
          Enter, Escape, Tab, BackSpace, Delete
          Up, Down, Left, Right
          Home, End, PageUp, PageDown
          F1 ~ F12
          A ~ Z（大写字母）
          Zero ~ Nine（数字键）
          SpaceBar

        Args:
            key:   UE FKey 名称，大小写敏感（如 "Enter"，不是 "enter"）
            shift: 是否按住 Shift
            ctrl:  是否按住 Ctrl
            alt:   是否按住 Alt
            text:  可选，同时附带发送的字符文本（在 key 事件后触发 char 事件）

        Returns:
            dict:
              success - 是否执行
              key     - 发送的按键名
              handled - Slate 是否处理了该事件
        """
        params: Dict[str, Any] = {
            "key":   key,
            "shift": shift,
            "ctrl":  ctrl,
            "alt":   alt,
        }
        if text:
            params["text"] = text
        return call_cpp_tools(unreal.MCPSlateTools.handle_send_key_press, params)

    # ─────────────────────────────────────────────────────────────────────────
    # 组合工具（Python 层实现的高级能力）
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_all_text_blocks(
        window_index: int = -1,
        window_title: str = "",
    ) -> Dict[str, Any]:
        """
        快速获取窗口中所有 STextBlock 的文本内容（slate_find_widgets_by_type 的快捷封装）。

        Args:
            window_index: 限定窗口索引（-1 搜索所有）
            window_title: 按标题限定窗口

        Returns:
            dict:
              count   - 找到的文本块数量
              texts   - list of {text, tag, depth, in_window}
        """
        params: Dict[str, Any] = {"type_name": "STextBlock", "max_depth": 12}
        if window_index >= 0:
            params["window_index"] = window_index
        if window_title:
            params["window_title"] = window_title

        raw = call_cpp_tools(unreal.MCPSlateTools.handle_find_widgets_by_type, params)
        widgets = raw.get("widgets", [])

        texts = [
            {
                "text":      w.get("text", ""),
                "tag":       w.get("tag", ""),
                "depth":     w.get("depth", 0),
                "in_window": w.get("in_window", ""),
            }
            for w in widgets
            if w.get("text", "").strip()  # 只返回非空文本
        ]

        return {
            "count": len(texts),
            "texts": texts,
        }

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_editor_ui_summary() -> Dict[str, Any]:
        """
        获取 Unreal Editor 当前 UI 状态的高层摘要，包括：
        - 所有顶层窗口列表
        - 每个窗口下第一层可见的 Tab/面板名称（通过 STextBlock 文本推断）

        适合 AI 快速了解当前编辑器 UI 全貌。

        Returns:
            dict:
              windows        - 窗口列表（同 slate_get_all_windows）
              active_window  - 当前激活窗口的标题
        """
        windows_result = call_cpp_tools(unreal.MCPSlateTools.handle_get_all_windows, {})
        windows = windows_result.get("windows", [])

        active_title = ""
        for w in windows:
            if w.get("is_focused") or w.get("is_active"):
                active_title = w.get("title", "")
                break

        return {
            "windows":       windows,
            "active_window": active_title,
            "window_count":  len(windows),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 窗口管理
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_active_window() -> Dict[str, Any]:
        """
        获取 Unreal Editor 当前激活（前台）顶层窗口的详细信息。

        Returns:
            dict:
              success - 是否成功
              window  - 窗口信息 {title, type, visible, x, y, width, height}
        """
        return call_cpp_tools(unreal.MCPSlateTools.handle_get_active_window, {})

    @mcp.game_thread_tool()
    def slate_move_window(
        x: float,
        y: float,
        window_index: int = -1,
        window_title: str = "",
    ) -> Dict[str, Any]:
        """
        将指定窗口移动到新的屏幕位置。不指定窗口时操作第一个可见正常窗口。

        Args:
            x:             目标屏幕 X 坐标（像素）
            y:             目标屏幕 Y 坐标（像素）
            window_index:  窗口索引（-1 表示不限定）
            window_title:  按标题关键字限定窗口（部分匹配）

        Returns:
            dict: success / window_title / new_x / new_y
        """
        params: Dict[str, Any] = {"x": x, "y": y}
        if window_index >= 0:
            params["window_index"] = window_index
        if window_title:
            params["window_title"] = window_title
        return call_cpp_tools(unreal.MCPSlateTools.handle_move_window, params)

    @mcp.game_thread_tool()
    def slate_resize_window(
        width: float,
        height: float,
        window_index: int = -1,
        window_title: str = "",
    ) -> Dict[str, Any]:
        """
        调整指定窗口的大小。不指定窗口时操作第一个可见正常窗口。

        Args:
            width:         新宽度（像素）
            height:        新高度（像素）
            window_index:  窗口索引（-1 表示不限定）
            window_title:  按标题关键字限定窗口（部分匹配）

        Returns:
            dict: success / window_title / new_width / new_height
        """
        params: Dict[str, Any] = {"width": width, "height": height}
        if window_index >= 0:
            params["window_index"] = window_index
        if window_title:
            params["window_title"] = window_title
        return call_cpp_tools(unreal.MCPSlateTools.handle_resize_window, params)

    @mcp.game_thread_tool()
    def slate_close_window(
        window_index: int = -1,
        window_title: str = "",
    ) -> Dict[str, Any]:
        """
        关闭（销毁）指定窗口。不指定时关闭当前激活窗口。
        注意：关闭主编辑器窗口会退出编辑器，请谨慎使用。

        Args:
            window_index:  窗口索引（-1 表示不限定）
            window_title:  按标题关键字限定窗口（部分匹配）

        Returns:
            dict: success / closed_window（关闭的窗口标题）
        """
        params: Dict[str, Any] = {}
        if window_index >= 0:
            params["window_index"] = window_index
        if window_title:
            params["window_title"] = window_title
        return call_cpp_tools(unreal.MCPSlateTools.handle_close_window, params)

    @mcp.game_thread_tool()
    def slate_close_dock_tab(
        tab_label: str = "",
        tab_id: str = "",
        window_title: str = "",
    ) -> Dict[str, Any]:
        """
        关闭指定 DockTab（用于 Project Settings / Plugins 等面板）。

        Args:
            tab_label:  Tab 显示标题（模糊匹配）
            tab_id:     Tab ID（如 "Plugins", "ProjectSettings"）
            window_title: 限定顶层窗口标题（可选）

        Returns:
            dict: success / tab_label / tab_id / in_window
        """
        params: Dict[str, Any] = {}
        if tab_label:
            params["tab_label"] = tab_label
        if tab_id:
            params["tab_id"] = tab_id
        if window_title:
            params["window_title"] = window_title
        return call_cpp_tools(unreal.MCPSlateTools.handle_close_dock_tab, params)

    @mcp.game_thread_tool()
    def slate_safe_close(
        tab_label: str = "",
        tab_id: str = "",
        window_title: str = "",
    ) -> Dict[str, Any]:
        """
        安全关闭：优先关闭 DockTab（如 Project Settings/Plugins）。
        若未提供 tab 信息，则仅在明确给出 window_title 时才关闭窗口。

        Args:
            tab_label:    Tab 显示标题（模糊匹配）
            tab_id:       Tab ID（如 "Plugins", "ProjectSettings"）
            window_title: 顶层窗口标题（仅当未提供 tab 信息时使用）

        Returns:
            dict: success / mode / detail
        """
        if tab_label or tab_id:
            res = call_cpp_tools(
                unreal.MCPSlateTools.handle_close_dock_tab,
                {"tab_label": tab_label, "tab_id": tab_id, "window_title": window_title},
            )
            res["mode"] = "dock_tab"
            return res

        if window_title:
            res = call_cpp_tools(
                unreal.MCPSlateTools.handle_close_window,
                {"window_title": window_title},
            )
            res["mode"] = "window"
            return res

        return {
            "success": False,
            "error": "Missing tab_label/tab_id or window_title",
            "mode": "none",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 焦点管理
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_focused_widget() -> Dict[str, Any]:
        """
        获取当前拥有键盘焦点的 Widget 信息。

        Returns:
            dict:
              success   - 是否有焦点 Widget
              type      - Widget 类型名（如 SEditableText、SButton 等）
              tag       - Widget 的 Tag
              text      - 若为文本控件则包含当前文本内容
        """
        return call_cpp_tools(unreal.MCPSlateTools.handle_get_focused_widget, {})

    @mcp.game_thread_tool()
    def slate_set_keyboard_focus(x: float, y: float) -> Dict[str, Any]:
        """
        将键盘焦点设置到指定屏幕坐标处的 Widget。
        常用于点击文本框后再调用 slate_send_text_input 输入文字。

        Args:
            x: 屏幕 X 坐标（像素）
            y: 屏幕 Y 坐标（像素）

        Returns:
            dict: success / focused_widget（被聚焦的 Widget 类型）
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_set_keyboard_focus,
            {"x": x, "y": y},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Tab / 面板管理
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.game_thread_tool()
    def slate_invoke_tab(tab_id: str) -> Dict[str, Any]:
        """
        通过 Tab ID 打开或切换到指定的 Unreal Editor 面板。
        若面板已打开则将其置于前台；若尚未打开则尝试创建并打开。

        常用 Tab ID 参考：
          OutputLog        - 输出日志
          ContentBrowser1  - 内容浏览器
          LevelEditor      - 关卡编辑器视口
          WorldOutliner    - 世界大纲
          DetailsView      - 详情面板
          MessageLog       - 消息日志
          Sequencer        - 序列器
          StatsViewer      - 统计信息
          FindResults      - 查找结果

        Args:
            tab_id: Editor Tab 的唯一标识字符串（区分大小写）

        Returns:
            dict: success / tab_id / tab_label / tab_role / is_foreground
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_invoke_tab,
            {"tab_id": tab_id},
        )

    @mcp.domain_tool("slate", game_thread=True)
    def slate_get_all_dock_tabs() -> Dict[str, Any]:
        """
        遍历所有顶层窗口的 Widget 树，收集当前打开的所有 DockTab 信息。

        Returns:
            dict:
              success - 是否成功
              count   - Tab 总数
              tabs    - list of {label, role, is_foreground, in_window}
                label        - Tab 显示标签文本
                role         - Tab 角色 (MajorTab/PanelTab/DocumentTab/NomadTab)
                is_foreground- 是否为前台激活 Tab
                in_window    - 所在窗口标题
        """
        return call_cpp_tools(unreal.MCPSlateTools.handle_get_all_dock_tabs, {})

    # ─────────────────────────────────────────────────────────────────────────
    # 滚动
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.game_thread_tool()
    def slate_scroll_at_position(
        x: float,
        y: float,
        delta: float,
    ) -> Dict[str, Any]:
        """
        在指定屏幕坐标模拟鼠标滚轮滚动事件。
        适用于滚动 ListView、TreeView、ScrollBox 等可滚动控件。

        Args:
            x:     屏幕 X 坐标（像素）
            y:     屏幕 Y 坐标（像素）
            delta: 滚动量（正值向上/向前，负值向下/向后）
                   建议绝对值范围 1–10；值越大滚动越多

        Returns:
            dict: success / x / y / delta
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_scroll_at_position,
            {"x": x, "y": y, "delta": delta},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 通知
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.game_thread_tool()
    def slate_show_notification(
        message: str,
        type: str = "Info",
        duration: float = 3.0,
        with_button: bool = False,
    ) -> Dict[str, Any]:
        """
        在 Unreal Editor 右下角弹出 Slate 通知气泡。

        Args:
            message:     通知正文（支持普通文本）
            type:        通知类型，影响图标颜色：
                           "Info"    - 默认，无特殊图标
                           "Success" - 绿色对勾
                           "Failure" - 红色叉号
                           "Pending" - 旋转加载图标
            duration:    自动消失前显示的秒数（默认 3.0）
            with_button: 是否附带 "Dismiss" 关闭按钮（若为 True，不会自动消失）

        Returns:
            dict: success / message / type / duration
        """
        return call_cpp_tools(
            unreal.MCPSlateTools.handle_show_notification,
            {
                "message":     message,
                "type":        type,
                "duration":    duration,
                "with_button": with_button,
            },
        )
