import os
import re
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, List, Tuple

import unreal
from foundation.mcp_app import UnrealMCP
from mcp.types import CallToolResult, TextContent


def _get_world() -> Optional[unreal.World]:
    try:
        editor_subsystem: unreal.UnrealEditorSubsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = editor_subsystem.get_game_world()
        if world:
            return world
        return editor_subsystem.get_editor_world()
    except Exception:
        return None


def _default_ubt_log_path() -> str:
    lad = os.environ.get("LOCALAPPDATA", "")
    if not lad:
        return ""
    return os.path.join(lad, "UnrealBuildTool", "Log.txt")

def _default_ubt_log_json_path() -> str:
    lad = os.environ.get("LOCALAPPDATA", "")
    if not lad:
        return ""
    return os.path.join(lad, "UnrealBuildTool", "Log.json")


def _safe_getsize(path: str) -> int:
    try:
        return os.path.getsize(path)
    except Exception:
        return 0


def _read_incremental_text(path: str, start_offset: int) -> tuple[str, int]:
    if not path or not os.path.isfile(path):
        return "", start_offset
    try:
        size = os.path.getsize(path)
        if size <= start_offset:
            return "", start_offset
        with open(path, "rb") as f:
            f.seek(start_offset)
            data = f.read()
        text = data.decode("utf-8", errors="replace")
        return text, size
    except Exception as e:
        return f"[incremental_read_failed] {e}\n", start_offset


def _tail_text(path: str, *, max_bytes: int = 256 * 1024) -> str:
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start)
            data = f.read()
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[tail_read_failed] {e}"


def _parse_ubt_json_lines(text: str) -> List[Dict[str, Any]]:
    """
    UBT Log.json 通常是“每行一个 JSON 对象”（JSONL）。
    """
    out: List[Dict[str, Any]] = []
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _parse_iso_time(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        # examples:
        # 2026-01-11T11:14:06
        # 2026-01-11T11:14:06Z
        v = value.strip()
        if v.endswith("Z"):
            v = v[:-1]
        dt = datetime.fromisoformat(v)
        # assume UTC when no tzinfo (UBT uses Z/UTC in practice)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


_MSVC_ERROR_RE = re.compile(r"\berror\s+(C\d{4})\b", re.IGNORECASE)
_MSVC_WARNING_RE = re.compile(r"\bwarning\s+(C\d{4})\b", re.IGNORECASE)
_LNK_ERROR_RE = re.compile(r"\b(LNK\d{4})\b", re.IGNORECASE)


def _analyze_build_log_text(text: str, *, max_items: int = 80) -> Dict[str, Any]:
    """
    对 UBT 日志文本做“轻量诊断”：抓取错误/警告的代表行，以及常见 MSVC/LNK 编码。
    """
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    codes: Dict[str, int] = {}

    if not text:
        return {"errors": errors, "warnings": warnings, "codes": codes}

    for line in text.splitlines():
        ll = line.lower()
        if "error" in ll:
            m = _MSVC_ERROR_RE.search(line) or _LNK_ERROR_RE.search(line)
            code = (m.group(1) if m else "").upper()
            if code:
                codes[code] = codes.get(code, 0) + 1
            if len(errors) < max_items:
                errors.append({"line": line, "code": code})
            continue

        if "warning" in ll:
            m = _MSVC_WARNING_RE.search(line)
            code = (m.group(1) if m else "").upper()
            if code:
                codes[code] = codes.get(code, 0) + 1
            if len(warnings) < max_items:
                warnings.append({"line": line, "code": code})
            continue

    return {"errors": errors, "warnings": warnings, "codes": codes}


def register_livecoding_tools(mcp: UnrealMCP):
    @mcp.game_thread_tool(
        "livecoding_compile_and_get_ubt_log",
        description="触发 UE LiveCoding 编译（Compile/CompileSync），读取 UnrealBuildTool\\Log.txt/Log.json，并解析汇总编译错误/警告",
    )
    async def livecoding_compile_and_get_ubt_log(
        compile_sync: bool = True,
        ubt_log_path: str = "",
        ubt_log_json_path: str = "",
        timeout_seconds: float = 120.0,
        settle_frames: int = 30,
        tail_bytes: int = 256 * 1024,
        json_tail_bytes: int = 512 * 1024,
    ) -> CallToolResult:
        world = _get_world()
        if not world:
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text="未找到有效 World，无法执行 LiveCoding 控制台命令。")],
                structuredContent={"result": "error", "reason": "world_not_found"},
            )

        try:
            timeout_seconds = float(timeout_seconds) if timeout_seconds is not None else 120.0
            settle_frames = int(settle_frames) if settle_frames is not None else 30
            tail_bytes = int(tail_bytes) if tail_bytes is not None else 256 * 1024
            json_tail_bytes = int(json_tail_bytes) if json_tail_bytes is not None else 512 * 1024
        except Exception:
            timeout_seconds = 120.0
            settle_frames = 30
            tail_bytes = 256 * 1024
            json_tail_bytes = 512 * 1024

        ubt_log_path = (ubt_log_path or "").strip() or _default_ubt_log_path()
        ubt_log_json_path = (ubt_log_json_path or "").strip() or _default_ubt_log_json_path()
        start_offset = _safe_getsize(ubt_log_path) if ubt_log_path else 0
        # JSON 日志经常会被重建/滚动，offset 增量不稳定；用 tail+时间过滤更可靠
        compile_start_utc = datetime.now(timezone.utc)

        cmd = "LiveCoding.CompileSync" if bool(compile_sync) else "LiveCoding.Compile"
        unreal.log(f"[mcp] {cmd} (ubt_log={ubt_log_path}, ubt_log_json={ubt_log_json_path}, start_offset={start_offset})")
        try:
            unreal.SystemLibrary.execute_console_command(world, cmd)  # type: ignore
        except Exception as e:
            return CallToolResult(
                isError=True,
                content=[TextContent(type="text", text=f"执行控制台命令失败：{e}")],
                structuredContent={"result": "error", "reason": "execute_console_command_failed", "error": f"{e}"},
            )

        waited_frames = 0
        stable_frames = 0
        last_len = 0
        chunks: list[str] = []
        start_ts = time.time()

        # 如果是 Compile（异步），UBT 日志写入会滞后；即便是 CompileSync，也可能有 flush 延迟。
        while True:
            waited_frames += 1
            await mcp.next_frame()

            text, new_off = _read_incremental_text(ubt_log_path, start_offset)
            if text:
                chunks.append(text)
                start_offset = new_off

            inc = "".join(chunks)
            if len(inc) == last_len:
                stable_frames += 1
            else:
                stable_frames = 0
                last_len = len(inc)

            # 结束条件：日志稳定一段时间；或超时
            if settle_frames > 0 and stable_frames >= settle_frames:
                break
            if timeout_seconds > 0 and (time.time() - start_ts) >= timeout_seconds:
                break

        incremental = "".join(chunks)
        tail = _tail_text(ubt_log_path, max_bytes=tail_bytes) if ubt_log_path else ""
        json_tail = _tail_text(ubt_log_json_path, max_bytes=json_tail_bytes) if ubt_log_json_path else ""

        # --- error analysis ---
        json_objs = _parse_ubt_json_lines(json_tail)
        # 用时间做“宽松过滤”（2 分钟窗口），避免 tail 太大时夹杂旧编译日志
        json_recent: List[Dict[str, Any]] = []
        window_start = compile_start_utc - timedelta(seconds=120)

        for obj in json_objs:
            t = _parse_iso_time(str(obj.get("time", "")))
            if t is None:
                continue
            if t >= window_start:
                json_recent.append(obj)

        # Build a plain-text slice from JSON for analysis (message field)
        json_text_lines: List[str] = []
        for obj in json_recent[-2000:]:
            msg = obj.get("message", "")
            if isinstance(msg, str) and msg:
                lvl = str(obj.get("level", ""))
                tm = str(obj.get("time", ""))
                json_text_lines.append(f"[{tm}][{lvl}] {msg}")
        json_text = "\n".join(json_text_lines)

        analysis_src = incremental or tail or json_text
        analysis = _analyze_build_log_text(analysis_src)

        error_count = len(analysis.get("errors", []))
        warning_count = len(analysis.get("warnings", []))

        payload: Dict[str, Any] = {
            "result": "ok",
            "command": cmd,
            "ubt_log_path": ubt_log_path,
            "ubt_log_json_path": ubt_log_json_path,
            "start_offset": start_offset,
            "waited_frames": waited_frames,
            "incremental_log": incremental,
            "tail_log": tail,
            "json_tail_log": json_tail,
            "analysis": {
                "error_count": error_count,
                "warning_count": warning_count,
                "codes": analysis.get("codes", {}),
                "errors": analysis.get("errors", []),
                "warnings": analysis.get("warnings", []),
            },
        }

        text_out = "\n".join(
            [
                f"result: ok",
                f"command: {cmd}",
                f"ubt_log_path: {ubt_log_path}",
                f"ubt_log_json_path: {ubt_log_json_path}",
                f"waited_frames: {waited_frames}",
                f"errors: {error_count}",
                f"warnings: {warning_count}",
                "",
                "=== ubt_log_incremental ===",
                incremental if incremental else "[empty_incremental]",
                "",
                "=== ubt_log_tail ===",
                tail if tail else "[empty_tail]",
                "",
                "=== ubt_log_json_tail ===",
                json_tail[-8000:] if json_tail else "[empty_json_tail]",
            ]
        )

        return CallToolResult(
            content=[TextContent(type="text", text=text_out)],
            structuredContent=payload,
        )

