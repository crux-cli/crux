"""Root conftest: ensure PYTHONPATH uses absolute paths for subprocess tests."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def pytest_configure(config):
    """Make PYTHONPATH absolute so subprocesses spawned in tmp dirs can import crux_cli."""
    src = str(REPO_ROOT / "src")
    existing = os.environ.get("PYTHONPATH", "")
    parts = [p for p in existing.split(os.pathsep) if p] if existing else []
    # Ensure the absolute src path is first
    if src not in parts:
        parts.insert(0, src)
    os.environ["PYTHONPATH"] = os.pathsep.join(parts)
