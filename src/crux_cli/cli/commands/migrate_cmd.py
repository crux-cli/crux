"""``crux migrate`` — convert a v1 crux.json into a v2 harness + pointer."""

from __future__ import annotations

import argparse
from pathlib import Path

from crux_cli.migrate_v1 import migrate_cwd


def cmd_migrate(args: argparse.Namespace) -> None:
    name = migrate_cwd(Path.cwd(), name=getattr(args, "name", None))
    print(f"migrate: created harness {name}@v1 and crux.toml pointer")
