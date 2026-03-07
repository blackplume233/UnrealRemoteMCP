
from RemoteMCP.Content.Python.foundation.mcp_app import UnrealMCP
from foundation import global_context
from mcp.server.fastmcp import FastMCP
import tools.common_tools as common_register
import tools.prompt as prompt_register
import tools.resource as resource_register
import tools.edit_tools as edit_register
import tools.livecoding_tools as livecoding_register
import tools.edgraph_tools as edgraph_register
import tools.behaviortree_tools as bt_register
import tools.slate_tools as slate_register
import unreal
import types
from typing import Any


def register_all_tools(mcp:UnrealMCP):
    # AI(GPT-5.2): 接入 EdGraph/BehaviorTree 工具注册，使其随 init_mcp() / reload_all_tools() 生效。
    # 兼容：如果当前运行的 UnrealMCP 实例来自旧版本（缺少 domain meta API），在这里动态补齐。
    def _ensure_domain_meta_api(mcp_obj: FastMCP) -> None:
        if not hasattr(mcp_obj, "_domain_meta"):
            try:
                setattr(mcp_obj, "_domain_meta", {})
            except Exception:
                pass

        def _set_domain_description(self_ref: Any, domain: str, description: str) -> None:
            d = (domain or "").strip()
            if not d:
                return
            meta = getattr(self_ref, "_domain_meta", None)
            if meta is None or not isinstance(meta, dict):
                meta = {}
                setattr(self_ref, "_domain_meta", meta)
            meta[d] = {"description": description or ""}
            # 确保 domain dict 存在
            tools_map = getattr(self_ref, "_domain_tools", None)
            if isinstance(tools_map, dict) and d not in tools_map:
                tools_map[d] = {}

        def _get_domain_description(self_ref: Any, domain: str) -> str:
            d = (domain or "").strip()
            if not d:
                return ""
            meta = getattr(self_ref, "_domain_meta", None)
            if isinstance(meta, dict):
                try:
                    return str((meta.get(d, {}) or {}).get("description", "") or "")
                except Exception:
                    return ""
            return ""

        def _list_domains_info(self_ref: Any):
            out = []
            try:
                domains = self_ref.list_domains() if hasattr(self_ref, "list_domains") else []
                for d in domains:
                    out.append({"domain": d, "description": _get_domain_description(self_ref, d)})
            except Exception:
                pass
            return out

        if not hasattr(mcp_obj, "set_domain_description"):
            mcp_obj.set_domain_description = types.MethodType(_set_domain_description, mcp_obj)  # type: ignore[attr-defined]
        if not hasattr(mcp_obj, "get_domain_description"):
            mcp_obj.get_domain_description = types.MethodType(_get_domain_description, mcp_obj)  # type: ignore[attr-defined]
        if not hasattr(mcp_obj, "list_domains_info"):
            mcp_obj.list_domains_info = types.MethodType(_list_domains_info, mcp_obj)  # type: ignore[attr-defined]

    _ensure_domain_meta_api(mcp)

    common_register.register_common_tools(mcp)
    resource_register.register_resource(mcp)
    edit_register.register_edit_tool(mcp)
    livecoding_register.register_livecoding_tools(mcp)
    prompt_register.register_prompt(mcp)
    edgraph_register.register_edgraph_tools(mcp)
    bt_register.register_behaviortree_tools(mcp)
    slate_register.register_slate_tools(mcp)
    
def reload_all_tools(mcp:UnrealMCP):
    global_context.reload_all_tool_modules()
    register_all_tools(mcp)
    unreal.log("reload all tools")