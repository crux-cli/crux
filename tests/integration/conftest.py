"""Fixtures for integration tests — runs crux as a real subprocess."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CRUX_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = CRUX_ROOT / "tests" / "fixtures"


@pytest.fixture
def crux_env(tmp_path):
    """
    Create a minimal Crux tree in tmp_path and return an env dict suitable for
    passing to subprocess.run so that crux uses this tree for all I/O.
    """
    marketplace_dir = tmp_path / "marketplace"
    mcp_dir = marketplace_dir / "mcps"
    (mcp_dir / "launchers").mkdir(parents=True)
    (marketplace_dir / "skills").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "sandbox").mkdir()

    # Install shared launcher scripts from bundled package data
    from crux_cli.setup_crux import _BUNDLED_LAUNCHERS

    launchers_dest = tmp_path / "launchers"
    launchers_dest.mkdir(parents=True, exist_ok=True)
    for script in _BUNDLED_LAUNCHERS.glob("*.sh"):
        target = launchers_dest / script.name
        shutil.copy2(script, target)
        target.chmod(0o755)

    shutil.copy(
        FIXTURES_DIR / "marketplace_minimal.json",
        marketplace_dir / "marketplace.json",
    )

    # Also seed registry.json from the marketplace fixture for the new CLI
    with open(FIXTURES_DIR / "marketplace_minimal.json") as f:
        manifest = json.load(f)
    registry = {
        "version": "1.0.0",
        "mcp_definitions": manifest.get("mcp_definitions", {}),
        "skill_definitions": manifest.get("skill_definitions", {}),
    }
    (tmp_path / "registry.json").write_text(json.dumps(registry, indent=2))

    env = os.environ.copy()
    env["CRUX_TEST_ROOT"] = str(tmp_path)
    return env, tmp_path


def run_crux(*args, env, cwd=None, input=None):
    """Run crux CLI with the given args and test env. Returns CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "crux_cli.cli.main", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        input=input,
    )
