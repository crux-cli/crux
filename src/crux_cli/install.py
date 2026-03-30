"""Package installation and dependency setup for MCP servers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def install_npm_package(package: str) -> tuple[bool, str]:
    """Install an npm package globally via npm install -g.

    Returns (ok, error_message).
    """
    try:
        result = subprocess.run(  # noqa: S603
            ["npm", "install", "-g", package],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "E404" in stderr or "404" in stderr:
                return False, f"package '{package}' not found in npm registry"
            return False, f"npm install failed: {stderr[:300]}"
        return True, ""
    except FileNotFoundError:
        return True, ""  # npm not installed, skip
    except subprocess.TimeoutExpired:
        return True, ""  # timeout, skip


def install_uv_package(package: str) -> tuple[bool, str]:
    """Install a Python package permanently via uv tool install.

    Returns (ok, error_message).
    """
    try:
        result = subprocess.run(  # noqa: S603
            ["uv", "tool", "install", package],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "not found" in stderr.lower() or "no such" in stderr.lower():
                return False, f"package '{package}' not found on PyPI"
            if "No solution found" in stderr or "yanked" in stderr.lower():
                return False, f"package '{package}' not installable (no available versions)"
            return False, f"uv tool install failed: {stderr[:300]}"
        return True, ""
    except FileNotFoundError:
        return True, ""  # uv not installed, skip
    except subprocess.TimeoutExpired:
        return True, ""  # timeout, skip


def detect_and_install_deps(dest: Path, entry: dict) -> tuple[bool, str]:
    """Auto-detect project type and install dependencies.

    Returns (ok, error_message). Updates entry with build_cmd if applicable.
    """
    pkg_json = dest / "package.json"
    pyproject = dest / "pyproject.toml"
    requirements = dest / "requirements.txt"

    if pkg_json.exists():
        return _install_npm_deps(dest, entry)
    elif pyproject.exists():
        return _install_uv_sync(dest)
    elif requirements.exists():
        return _install_uv_requirements(dest)

    return True, ""  # No recognized project files


def _install_npm_deps(dest: Path, entry: dict) -> tuple[bool, str]:
    """Run npm install and optionally npm run build."""
    print("  Installing npm dependencies...")
    result = subprocess.run(  # noqa: S603
        ["npm", "install"],  # noqa: S607
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False, f"npm install failed: {result.stderr.strip()[:300]}"
    print("  npm install complete")

    with open(dest / "package.json") as f:
        pkg = json.load(f)
    if "build" in pkg.get("scripts", {}):
        entry["build_cmd"] = "npm install && npm run build"
        print("  Running build...")
        build = subprocess.run(  # noqa: S603
            ["npm", "run", "build"],  # noqa: S607
            cwd=dest,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if build.returncode != 0:
            return False, f"npm build failed: {build.stderr.strip()[:300]}"
        print("  Build complete")

    return True, ""


def _install_uv_sync(dest: Path) -> tuple[bool, str]:
    """Run uv sync for pyproject.toml projects."""
    print("  Installing Python dependencies (uv sync)...")
    result = subprocess.run(  # noqa: S603
        ["uv", "sync"],  # noqa: S607
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False, f"uv sync failed: {result.stderr.strip()[:300]}"
    print("  uv sync complete")
    return True, ""


def _install_uv_requirements(dest: Path) -> tuple[bool, str]:
    """Create venv and install from requirements.txt."""
    print("  Installing Python dependencies (requirements.txt)...")
    venv = subprocess.run(  # noqa: S603
        ["uv", "venv"],  # noqa: S607
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if venv.returncode != 0:
        return False, f"uv venv failed: {venv.stderr.strip()[:300]}"

    install = subprocess.run(  # noqa: S603
        ["uv", "pip", "install", "-r", "requirements.txt"],  # noqa: S607
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if install.returncode != 0:
        return False, f"uv pip install failed: {install.stderr.strip()[:300]}"
    print("  Dependencies installed")
    return True, ""


def rollback_mcp_add(name: str, entry: dict) -> None:
    """Roll back a failed mcp add: remove registry entry, clean up files and packages."""
    from crux_cli.manifest import load_registry, save_registry

    # Remove from registry
    reg = load_registry()
    if name in reg.get("mcp_definitions", {}):
        del reg["mcp_definitions"][name]
        save_registry(reg)

    # Delete source directory if under crux home
    source_dir = entry.get("source_dir")
    if source_dir:
        from crux_cli.paths import crux_home

        resolved = Path(source_dir).resolve()
        if resolved.exists() and str(resolved).startswith(str(crux_home().resolve())):
            import shutil

            shutil.rmtree(resolved)

    # Uninstall packages
    mcp_type = entry.get("type", "")
    if mcp_type == "uvx-package":
        pkg = entry.get("args", [""])[0]
        if pkg:
            subprocess.run(  # noqa: S603
                ["uv", "tool", "uninstall", pkg],  # noqa: S607
                capture_output=True,
                timeout=30,
            )
    elif mcp_type == "npm-package":
        args = entry.get("args", [])
        pkg = next((a for a in args if not a.startswith("-")), None)
        if pkg:
            subprocess.run(  # noqa: S603
                ["npm", "uninstall", "-g", pkg],  # noqa: S607
                capture_output=True,
                timeout=30,
            )
