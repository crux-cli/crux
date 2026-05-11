"""Integration test helpers — runs crux v2 as a real subprocess."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

CRUX_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def crux_env(tmp_path):
    """Return ``(env, root)`` suitable for ``run_crux``: a tmp root + env override."""
    env = os.environ.copy()
    env["CRUX_TEST_ROOT"] = str(tmp_path)
    env["HOME"] = str(tmp_path / "home")
    env.pop("CRUX_HOME", None)
    (tmp_path / "home").mkdir(exist_ok=True)
    return env, tmp_path


def run_crux(*args, env, cwd=None, input=None):
    """Run ``python -m crux_cli`` with *args*. Returns a CompletedProcess."""
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "crux_cli", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        input=input,
    )
