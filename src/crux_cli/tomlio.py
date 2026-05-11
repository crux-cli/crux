"""Minimal TOML I/O.

Reading delegates to stdlib ``tomllib``. Writing supports the small subset
Crux emits: strings, ints, bools, flat lists of those types, and one level
of nested tables. Anything more exotic should be modeled as a nested table.
"""

from __future__ import annotations

import tempfile
import tomllib
from pathlib import Path
from typing import Any


def load_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file into a dict."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def _fmt_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(v, list):
        return "[" + ", ".join(_fmt_value(x) for x in v) + "]"
    raise TypeError(f"Unsupported TOML value: {type(v).__name__}")


def dump_toml(path: Path, data: dict[str, Any]) -> None:
    """Atomically write a dict as TOML.

    Top-level scalar/list keys come first, then nested tables.
    Empty tables are emitted as ``[name]`` headers with no body.
    """
    lines: list[str] = []
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    for k, v in scalars.items():
        lines.append(f"{k} = {_fmt_value(v)}")
    for table_name, table in tables.items():
        if lines:
            lines.append("")
        lines.append(f"[{table_name}]")
        for k, v in table.items():
            lines.append(f"{k} = {_fmt_value(v)}")
    content = "\n".join(lines) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            f.write(content)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
