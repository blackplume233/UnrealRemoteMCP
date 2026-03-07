from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import unreal
from foundation.mcp_app import UnrealMCP
from foundation.utility import like_str_parameter


def _parse_maybe_json(v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return v
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return json.loads(s)
            except Exception:
                return v
    return v


def _to_jsonable(v: Any, depth: int = 0, seen: Optional[set[int]] = None) -> Any:
    """将 UE/Python 任意值转换为 JSON-safe（避免 MCP structuredContent 序列化失败）。"""
    if seen is None:
        seen = set()
    if depth >= 6:
        return str(v)

    try:
        obj_id = id(v)
        if obj_id in seen:
            return "<circular_ref>"
        seen.add(obj_id)
    except Exception:
        pass

    if v is None or isinstance(v, (str, int, float, bool)):
        return v

    if isinstance(v, (list, tuple, set)):
        return [_to_jsonable(x, depth + 1, seen) for x in v]
    if isinstance(v, dict):
        return {str(k): _to_jsonable(val, depth + 1, seen) for k, val in v.items()}

    # UE 常见结构/对象兜底
    if hasattr(v, "to_tuple"):
        try:
            return _to_jsonable(list(v.to_tuple()), depth + 1, seen)
        except Exception:
            pass
    if hasattr(v, "get_path_name"):
        try:
            return v.get_path_name()
        except Exception:
            pass
    if hasattr(v, "get_name"):
        try:
            return v.get_name()
        except Exception:
            pass
    try:
        return str(v)
    except Exception as e:
        return f"<unserializable:{type(v)}:{e}>"


def _load_uobject(path: str):
    if not path:
        return None
    obj = None
    # 先尝试 load_object（可加载子对象路径，如 /Game/A.B:A_SubObj）
    try:
        obj = unreal.load_object(None, path)
    except Exception:
        obj = None
    if obj:
        return obj
    # 再尝试 load_asset（主要用于资产路径）
    try:
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        return None


def _obj_path(obj: Any) -> str:
    if obj is None:
        return ""
    if hasattr(obj, "get_path_name"):
        try:
            return obj.get_path_name()
        except Exception:
            pass
    return str(obj)


def _is_edgraph(obj: Any) -> bool:
    try:
        return isinstance(obj, unreal.EdGraph)
    except Exception:
        # 某些版本 python wrapper 的 isinstance 可能失效，这里用 class 名兜底
        try:
            return "EdGraph" in obj.get_class().get_name()
        except Exception:
            return False


def _is_edgraph_node(obj: Any) -> bool:
    try:
        return isinstance(obj, unreal.EdGraphNode)
    except Exception:
        try:
            return "EdGraphNode" in obj.get_class().get_name()
        except Exception:
            return False


def _get_editor_prop(obj: Any, prop: str, default: Any = None) -> Any:
    try:
        return obj.get_editor_property(prop)
    except Exception:
        return default


def _set_editor_prop(obj: Any, prop: str, value: Any) -> Tuple[bool, str]:
    try:
        obj.set_editor_property(prop, value)
        return True, ""
    except Exception as e:
        return False, str(e)


def _get_graph_nodes(graph: Any) -> List[Any]:
    # UEdGraph.Nodes
    nodes = _get_editor_prop(graph, "nodes", None)
    if nodes is None:
        # 兜底：某些 wrapper 可能暴露为 graph.nodes
        nodes = getattr(graph, "nodes", None)
    if nodes is None:
        return []
    try:
        return list(nodes)
    except Exception:
        return []


def _node_guid_str(node: Any) -> str:
    # 典型属性：NodeGuid / node_guid（不同版本/绑定可能不同）
    for key in ("node_guid", "NodeGuid", "nodeGuid", "guid"):
        v = _get_editor_prop(node, key, None)
        if v is None:
            continue
        try:
            return str(v)
        except Exception:
            pass
    return ""


def _find_node(graph: Any, *, node_path: str = "", node_guid: str = "", node_name: str = "") -> Any:
    node_path = (node_path or "").strip()
    node_guid = (node_guid or "").strip()
    node_name = (node_name or "").strip()

    if node_path:
        n = _load_uobject(node_path)
        if n and _is_edgraph_node(n):
            return n

    for n in _get_graph_nodes(graph):
        if not n:
            continue
        if node_guid and _node_guid_str(n) == node_guid:
            return n
        if node_name:
            try:
                if n.get_name() == node_name:
                    return n
            except Exception:
                pass
    return None


def _get_node_pins(node: Any) -> List[Any]:
    # UEdGraphNode.Pins
    pins = _get_editor_prop(node, "pins", None)
    if pins is None:
        pins = getattr(node, "pins", None)
    if pins is None:
        try:
            pins = node.get_pins()
        except Exception:
            pins = None
    if pins is None:
        return []
    try:
        return list(pins)
    except Exception:
        return []


def _pin_name(pin: Any) -> str:
    for key in ("pin_name", "PinName", "name"):
        v = getattr(pin, key, None)
        if v is None:
            v = _get_editor_prop(pin, key, None)
        if v is None:
            continue
        try:
            return str(v)
        except Exception:
            pass
    # 有些版本需要调用 get_name
    if hasattr(pin, "get_name"):
        try:
            return str(pin.get_name())
        except Exception:
            pass
    return ""


def _pin_direction(pin: Any) -> str:
    for key in ("direction", "Direction", "pin_direction", "PinDirection"):
        v = getattr(pin, key, None)
        if v is None:
            v = _get_editor_prop(pin, key, None)
        if v is None:
            continue
        try:
            return str(v)
        except Exception:
            pass
    return ""


def _pin_linked_to(pin: Any) -> List[Any]:
    for key in ("linked_to", "LinkedTo"):
        v = getattr(pin, key, None)
        if v is None:
            v = _get_editor_prop(pin, key, None)
        if v is None:
            continue
        try:
            return list(v)
        except Exception:
            return []
    # method fallback
    if hasattr(pin, "get_linked_to"):
        try:
            return list(pin.get_linked_to())
        except Exception:
            return []
    return []


def _find_pin(node: Any, pin_name: str, direction: str | None = None) -> Any:
    pin_name = (pin_name or "").strip()
    direction = (direction or "").strip() if direction is not None else None
    if not pin_name:
        return None
    for p in _get_node_pins(node):
        if not p:
            continue
        if _pin_name(p) != pin_name:
            continue
        if direction is not None and direction and _pin_direction(p) != direction:
            continue
        return p
    return None


def _serialize_node(node: Any, include_props: bool = False, max_props: int = 48) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "name": getattr(node, "get_name", lambda: "")(),
        "path": _obj_path(node),
        "class": node.get_class().get_name() if hasattr(node, "get_class") else str(type(node)),
        "guid": _node_guid_str(node),
        "pos": [
            _get_editor_prop(node, "node_pos_x", _get_editor_prop(node, "NodePosX", 0)),
            _get_editor_prop(node, "node_pos_y", _get_editor_prop(node, "NodePosY", 0)),
        ],
        "pins": [],
    }

    # pins 简要信息
    pins_out = []
    for p in _get_node_pins(node):
        if not p:
            continue
        pins_out.append(
            {
                "name": _pin_name(p),
                "direction": _pin_direction(p),
                "linked_to_count": len(_pin_linked_to(p)),
            }
        )
    out["pins"] = pins_out

    if include_props:
        props: Dict[str, Any] = {}
        count = 0
        for attr in dir(node):
            if count >= max_props:
                out["properties_truncated"] = True
                break
            if attr.startswith("_"):
                continue
            if attr in ("get_editor_property", "set_editor_property", "reset_editor_property", "is_editor_property_overridden"):
                continue
            if attr.startswith(("get_", "set_", "is_", "has_")):
                continue
            try:
                v = node.get_editor_property(attr)
            except Exception:
                continue
            props[attr] = _to_jsonable(v)
            count += 1
        out["properties"] = props

    return out


def _save_asset_if_needed(asset_path: str) -> Dict[str, Any]:
    asset_path = (asset_path or "").strip()
    if not asset_path:
        return {"saved": False, "reason": "asset_path empty"}
    ok = False
    try:
        ok = bool(unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False))
    except Exception as e:
        return {"saved": False, "error": str(e), "asset": asset_path}
    return {"saved": ok, "asset": asset_path}


def _discover_graphs_in_asset(asset: Any, max_results: int = 50) -> List[Any]:
    graphs: List[Any] = []

    # Blueprint 走官方库（最稳）
    try:
        if isinstance(asset, unreal.Blueprint):
            try:
                bgraphs = unreal.BlueprintEditorLibrary.get_all_graphs(asset)
                for g in bgraphs:
                    if g and _is_edgraph(g):
                        graphs.append(g)
            except Exception:
                pass
    except Exception:
        pass

    # 反射式扫描：尝试读取所有可能是 editor_property 的字段，抓出 EdGraph / list[EdGraph]
    # 注意：这是启发式，不保证覆盖所有资产类型，但对很多 Editor-only 资产有效。
    for attr in dir(asset):
        if len(graphs) >= max_results:
            break
        if attr.startswith("_"):
            continue
        if "graph" not in attr.lower():
            continue
        if attr in ("get_editor_property", "set_editor_property", "reset_editor_property", "is_editor_property_overridden"):
            continue
        try:
            v = asset.get_editor_property(attr)
        except Exception:
            continue
        if v is None:
            continue
        if _is_edgraph(v):
            graphs.append(v)
            continue
        if isinstance(v, (list, tuple)):
            for x in v:
                if x and _is_edgraph(x):
                    graphs.append(x)
                    if len(graphs) >= max_results:
                        break

    # 去重（按 path）
    uniq: Dict[str, Any] = {}
    for g in graphs:
        uniq[_obj_path(g)] = g
    return list(uniq.values())[:max_results]


def register_edgraph_tools(mcp: UnrealMCP):
    """
    一组通用 EdGraph/EdGraphNode CRUD 工具。

    设计目标：
    - 尽量泛化：只要你能拿到 graph 的 object path，就可以对节点/连线做增删改查。
    - 反射优先：对不同 UE 版本/不同图类型尽量多重 fallback。
    - 最小副作用：默认不保存资产；如需保存请显式传入 auto_save_asset_path。
    """

    mcp.set_domain_description(
        "edgraph",
        "通用 EdGraph 底层操作：发现图、节点增删改查、pin 连线枚举/连接/断开。可复用于蓝图图、行为树图等编辑器图。",
    )

    # AI(Claude Opus 4.5): 改为 domain_tool 注册，通过 get_dispatch/dispatch_tool 访问
    @mcp.domain_tool("edgraph")
    def edgraph_find_graphs_in_asset(asset_path: str, name_filter: str = "", max_results: int = 50) -> Dict[str, Any]:
        """
        在指定资产里“尽最大努力”发现 EdGraph（包含 Blueprint 特化 + 反射扫描）。

        Args:
            asset_path: 资产路径（/Game/...）
            name_filter: 可选，按 graph path/name 包含过滤（不区分大小写）
            max_results: 最多返回多少个
        """
        asset_path = like_str_parameter(asset_path, "asset_path", "").strip()
        name_filter = like_str_parameter(name_filter, "name_filter", "").strip().lower()
        max_results = int(max_results) if max_results is not None else 50

        asset = _load_uobject(asset_path)
        if not asset:
            return {"ok": False, "error": "asset not found", "asset_path": asset_path, "graphs": []}

        graphs = _discover_graphs_in_asset(asset, max_results=max_results)
        out = []
        for g in graphs:
            p = _obj_path(g)
            if name_filter and (name_filter not in p.lower()):
                continue
            out.append(
                {
                    "name": getattr(g, "get_name", lambda: "")(),
                    "path": p,
                    "class": g.get_class().get_name() if hasattr(g, "get_class") else str(type(g)),
                }
            )
        return {"ok": True, "asset": asset_path, "graphs": out}

    @mcp.domain_tool("edgraph")
    def edgraph_list_nodes(graph_path: str, include_node_properties: bool = False) -> Dict[str, Any]:
        """列出图内所有节点（可选带一部分 editor_property 快照）。"""
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        nodes = []
        for n in _get_graph_nodes(graph):
            if not n:
                continue
            nodes.append(_serialize_node(n, include_props=bool(include_node_properties)))
        return {
            "ok": True,
            "graph": {"name": graph.get_name(), "path": _obj_path(graph), "class": graph.get_class().get_name()},
            "node_count": len(nodes),
            "nodes": nodes,
        }

    @mcp.domain_tool("edgraph")
    def edgraph_get_node(
        graph_path: str,
        node_guid: str = "",
        node_name: str = "",
        node_path: str = "",
        include_node_properties: bool = True,
    ) -> Dict[str, Any]:
        """按 guid/name/path 查询单个节点。"""
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        node = _find_node(graph, node_path=node_path, node_guid=node_guid, node_name=node_name)
        if not node:
            return {"ok": False, "error": "node not found", "query": {"node_guid": node_guid, "node_name": node_name, "node_path": node_path}}

        return {"ok": True, "node": _serialize_node(node, include_props=bool(include_node_properties))}

    @mcp.domain_tool("edgraph")
    def edgraph_add_node(
        graph_path: str,
        node_class: str,
        node_name: str = "",
        pos_x: int = 0,
        pos_y: int = 0,
        properties: Any = None,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """
        在图内创建一个 EdGraphNode（尽力而为：不同图类型/不同 schema 可能还需要额外初始化）。

        Args:
            graph_path: EdGraph 的 object path（推荐用 edgraph_find_graphs_in_asset 找到）
            node_class: Unreal Python 里可用的节点类名（如 "EdGraphNode_Comment" / "BehaviorTreeGraphNode_Task" 等）
            node_name: 可选，节点 UObject 名（不保证影响显示名）
            pos_x/pos_y: 位置
            properties: 可选，dict 或 JSON 字符串，批量 set_editor_property
            auto_save_asset_path: 可选，传入则创建后保存该资产
        """
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        node_class = like_str_parameter(node_class, "node_class", "").strip()
        node_name = like_str_parameter(node_name, "node_name", "").strip()
        auto_save_asset_path = like_str_parameter(auto_save_asset_path, "auto_save_asset_path", "").strip()
        props = _parse_maybe_json(properties) if properties is not None else {}
        if props is None:
            props = {}
        if not isinstance(props, dict):
            return {"ok": False, "error": "properties must be dict/json", "properties_type": str(type(props))}

        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        cls = getattr(unreal, node_class, None)
        if cls is None:
            return {"ok": False, "error": "node_class not found in unreal module", "node_class": node_class}

        try:
            node = unreal.new_object(cls, outer=graph, name=node_name or None)
        except Exception as e:
            return {"ok": False, "error": f"new_object failed: {e}", "node_class": node_class}

        # 常见初始化
        _set_editor_prop(node, "node_pos_x", int(pos_x))
        _set_editor_prop(node, "node_pos_y", int(pos_y))
        if hasattr(node, "create_new_guid"):
            try:
                node.create_new_guid()
            except Exception:
                pass

        # 批量属性
        set_errors = {}
        for k, v in props.items():
            v2 = _parse_maybe_json(v)
            ok, err = _set_editor_prop(node, str(k), v2)
            if not ok:
                set_errors[str(k)] = err

        # 尝试挂到 graph
        added = False
        if hasattr(graph, "add_node"):
            # 多签名兜底
            for call in (
                lambda: graph.add_node(node),
                lambda: graph.add_node(node, True, False),
                lambda: graph.add_node(node, True, True),
            ):
                try:
                    call()
                    added = True
                    break
                except Exception:
                    continue

        if not added:
            # 兜底：直接 append nodes（某些图可能仍不会显示/需要 schema post-process）
            try:
                nodes = _get_graph_nodes(graph)
                nodes.append(node)
                graph.set_editor_property("nodes", nodes)
                added = True
            except Exception as e:
                return {"ok": False, "error": f"failed to attach node to graph: {e}", "node": _obj_path(node)}

        save_info = _save_asset_if_needed(auto_save_asset_path) if auto_save_asset_path else {"saved": False}

        return {
            "ok": True,
            "node": _serialize_node(node, include_props=False),
            "attached_to_graph": added,
            "set_property_errors": set_errors,
            "save": save_info,
        }

    @mcp.domain_tool("edgraph")
    def edgraph_delete_node(
        graph_path: str,
        node_guid: str = "",
        node_name: str = "",
        node_path: str = "",
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """从图内删除节点（按 guid/name/path）。"""
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        auto_save_asset_path = like_str_parameter(auto_save_asset_path, "auto_save_asset_path", "").strip()
        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        node = _find_node(graph, node_path=node_path, node_guid=node_guid, node_name=node_name)
        if not node:
            return {"ok": False, "error": "node not found", "query": {"node_guid": node_guid, "node_name": node_name, "node_path": node_path}}

        removed = False
        err = ""
        if hasattr(graph, "remove_node"):
            for call in (
                lambda: graph.remove_node(node),
                lambda: graph.remove_node(node, True),
                lambda: graph.remove_node(node, True, True),
            ):
                try:
                    call()
                    removed = True
                    break
                except Exception as e:
                    err = str(e)
        if not removed:
            try:
                nodes = _get_graph_nodes(graph)
                nodes = [x for x in nodes if _obj_path(x) != _obj_path(node)]
                graph.set_editor_property("nodes", nodes)
                removed = True
            except Exception as e:
                err = str(e)

        # 尽量销毁节点对象
        if hasattr(node, "destroy_node"):
            try:
                node.destroy_node()
            except Exception:
                pass

        save_info = _save_asset_if_needed(auto_save_asset_path) if auto_save_asset_path else {"saved": False}
        return {"ok": removed, "removed": removed, "error": err if not removed else "", "node": _obj_path(node), "save": save_info}

    @mcp.domain_tool("edgraph")
    def edgraph_set_node_properties(
        graph_path: str,
        properties: Any,
        node_guid: str = "",
        node_name: str = "",
        node_path: str = "",
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """
        修改节点属性（批量 set_editor_property）。

        properties: dict 或 JSON 字符串
        """
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        auto_save_asset_path = like_str_parameter(auto_save_asset_path, "auto_save_asset_path", "").strip()
        props = _parse_maybe_json(properties)
        if not isinstance(props, dict):
            return {"ok": False, "error": "properties must be dict/json", "properties_type": str(type(props))}

        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        node = _find_node(graph, node_path=node_path, node_guid=node_guid, node_name=node_name)
        if not node:
            return {"ok": False, "error": "node not found", "query": {"node_guid": node_guid, "node_name": node_name, "node_path": node_path}}

        errors: Dict[str, str] = {}
        applied: Dict[str, Any] = {}
        for k, v in props.items():
            v2 = _parse_maybe_json(v)
            ok, err = _set_editor_prop(node, str(k), v2)
            if ok:
                applied[str(k)] = _to_jsonable(v2)
            else:
                errors[str(k)] = err

        save_info = _save_asset_if_needed(auto_save_asset_path) if auto_save_asset_path else {"saved": False}
        return {"ok": True, "node": _serialize_node(node, include_props=False), "applied": applied, "errors": errors, "save": save_info}

    @mcp.domain_tool("edgraph")
    def edgraph_list_links(graph_path: str) -> Dict[str, Any]:
        """枚举图里所有 pin 连接（按 node/pin 去重后输出）。"""
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        links = []
        seen = set()
        for n in _get_graph_nodes(graph):
            if not n:
                continue
            n_guid = _node_guid_str(n)
            for p in _get_node_pins(n):
                if not p:
                    continue
                p_name = _pin_name(p)
                for lp in _pin_linked_to(p):
                    try:
                        other_node = lp.get_owning_node()
                    except Exception:
                        other_node = None
                    other_guid = _node_guid_str(other_node) if other_node else ""
                    other_pin_name = _pin_name(lp)
                    # 无向去重
                    key = tuple(sorted([(n_guid, p_name), (other_guid, other_pin_name)]))
                    if key in seen:
                        continue
                    seen.add(key)
                    links.append(
                        {
                            "a": {"node_guid": n_guid, "node_path": _obj_path(n), "pin": p_name},
                            "b": {"node_guid": other_guid, "node_path": _obj_path(other_node), "pin": other_pin_name},
                        }
                    )
        return {"ok": True, "graph": _obj_path(graph), "link_count": len(links), "links": links}

    @mcp.domain_tool("edgraph")
    def edgraph_connect_pins(
        graph_path: str,
        from_node_guid: str,
        from_pin: str,
        to_node_guid: str,
        to_pin: str,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """连接两个 pin（尽力调用 schema.try_create_connection 或 pin.make_link_to）。"""
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        auto_save_asset_path = like_str_parameter(auto_save_asset_path, "auto_save_asset_path", "").strip()

        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        n1 = _find_node(graph, node_guid=from_node_guid)
        n2 = _find_node(graph, node_guid=to_node_guid)
        if not n1 or not n2:
            return {"ok": False, "error": "node not found", "from_node_guid": from_node_guid, "to_node_guid": to_node_guid}

        p1 = _find_pin(n1, from_pin)
        p2 = _find_pin(n2, to_pin)
        if not p1 or not p2:
            return {"ok": False, "error": "pin not found", "from_pin": from_pin, "to_pin": to_pin}

        ok = False
        err = ""
        # schema 优先
        schema = None
        for getter in ("get_schema", "GetSchema"):
            if hasattr(graph, getter):
                try:
                    schema = getattr(graph, getter)()
                    break
                except Exception:
                    schema = None
        if schema is None:
            schema = _get_editor_prop(graph, "schema", _get_editor_prop(graph, "Schema", None))

        if schema is not None and hasattr(schema, "try_create_connection"):
            try:
                ok = bool(schema.try_create_connection(p1, p2))
            except Exception as e:
                err = str(e)

        if not ok:
            # pin method fallback
            for m in ("make_link_to", "MakeLinkTo"):
                if hasattr(p1, m):
                    try:
                        getattr(p1, m)(p2)
                        ok = True
                        err = ""
                        break
                    except Exception as e:
                        err = str(e)

        save_info = _save_asset_if_needed(auto_save_asset_path) if auto_save_asset_path else {"saved": False}
        return {"ok": ok, "error": err if not ok else "", "save": save_info}

    @mcp.domain_tool("edgraph")
    def edgraph_disconnect_pin(
        graph_path: str,
        node_guid: str,
        pin_name: str,
        auto_save_asset_path: str = "",
    ) -> Dict[str, Any]:
        """断开指定 pin 的所有连接。"""
        graph_path = like_str_parameter(graph_path, "graph_path", "").strip()
        auto_save_asset_path = like_str_parameter(auto_save_asset_path, "auto_save_asset_path", "").strip()
        graph = _load_uobject(graph_path)
        if not graph or not _is_edgraph(graph):
            return {"ok": False, "error": "graph not found or not EdGraph", "graph_path": graph_path}

        node = _find_node(graph, node_guid=node_guid)
        if not node:
            return {"ok": False, "error": "node not found", "node_guid": node_guid}
        pin = _find_pin(node, pin_name)
        if not pin:
            return {"ok": False, "error": "pin not found", "pin_name": pin_name}

        ok = False
        err = ""
        for m in ("break_all_pin_links", "BreakAllPinLinks"):
            if hasattr(pin, m):
                try:
                    getattr(pin, m)()
                    ok = True
                    err = ""
                    break
                except Exception as e:
                    err = str(e)
        if not ok:
            # 兜底：尝试逐个 break_link_to
            try:
                for lp in list(_pin_linked_to(pin)):
                    for m in ("break_link_to", "BreakLinkTo"):
                        if hasattr(pin, m):
                            getattr(pin, m)(lp)
                ok = True
            except Exception as e:
                err = str(e)

        save_info = _save_asset_if_needed(auto_save_asset_path) if auto_save_asset_path else {"saved": False}
        return {"ok": ok, "error": err if not ok else "", "save": save_info}

