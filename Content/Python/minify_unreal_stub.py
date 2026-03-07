"""
Generate a lightweight `unreal.pyi` from Unreal Engine generated `unreal.py`.

Why:
- UE's `Intermediate/PythonStub/unreal.py` can be >50MB mainly due to huge docstrings.
- Cursor/Pylance may fail to read/analyze such a large file.
- A `.pyi` stub (without docstrings) is much smaller and preferred by analyzers.

Usage (Windows):
  python tools/minify_unreal_stub.py --input "<YourProject>\\Intermediate\\PythonStub\\unreal.py"

By default, it writes `unreal.pyi` next to the input file.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


TRIPLE_QUOTES = ('"""', "'''")
PREFIXES = ("r", "u", "f", "b", "R", "U", "F", "B")


def _starts_triple_quoted_string(s: str) -> tuple[bool, str] | tuple[bool, None]:
    """Detect a triple-quoted string opener at the start of a statement."""
    s2 = s.lstrip()
    if not s2:
        return (False, None)

    # Accept optional prefix like r""" / u''' etc (single prefix is enough for UE stubs)
    if len(s2) >= 4 and s2[0] in PREFIXES and s2[1:4] in TRIPLE_QUOTES:
        return (True, s2[1:4])
    if s2[:3] in TRIPLE_QUOTES:
        return (True, s2[:3])
    return (False, None)


def minify_unreal_stub(input_path: Path, output_path: Path) -> None:
    """
    Remove triple-quoted docstring blocks from the stub file.

    Note:
    This is intentionally line-based and conservative: it only removes triple-quoted
    strings that appear as standalone statements (i.e. at the start of a line after
    indentation). UE stub files use docstrings in this form widely.
    """
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    in_triple = False
    closing = None

    # UE stub may contain BOM; utf-8-sig handles it.
    with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fin, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as fout:
        for line in fin:
            if not in_triple:
                starts, quote = _starts_triple_quoted_string(line)
                if starts and quote is not None:
                    # If the triple quote also closes on the same line, drop the line entirely.
                    # Otherwise, enter skip mode until we find the closing delimiter.
                    if line.count(quote) >= 2:
                        continue
                    in_triple = True
                    closing = quote
                    continue
                fout.write(line)
            else:
                # Skip until closing triple quote found.
                assert closing is not None
                if closing in line:
                    # If closing appears multiple times, we still just stop skipping.
                    in_triple = False
                    closing = None
                continue


def main() -> int:
    ap = argparse.ArgumentParser(description="Minify Unreal generated unreal.py into unreal.pyi (docstrings removed).")
    ap.add_argument(
        "--input",
        dest="input",
        default=None,
        help="Path to Intermediate/PythonStub/unreal.py. Default: ../../../../Intermediate/PythonStub/unreal.py (relative to this script).",
    )
    ap.add_argument(
        "--output",
        dest="output",
        default=None,
        help="Output .pyi path. Default: unreal.pyi next to input.",
    )
    args = ap.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        # tools/ -> Content/Python/ ; then follow the extraPaths in Python.code-workspace
        input_path = (Path(__file__).resolve().parent.parent / "../../../../Intermediate/PythonStub/unreal.py").resolve()

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".pyi")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    minify_unreal_stub(input_path, output_path)

    in_size = os.path.getsize(input_path)
    out_size = os.path.getsize(output_path)
    print(f"Generated: {output_path}")
    print(f"Input size : {in_size} bytes")
    print(f"Output size: {out_size} bytes")
    if out_size >= 52_428_800:
        print("WARNING: output is still >= 50MB; consider excluding more content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

