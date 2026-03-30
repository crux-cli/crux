# MCP Add Install and Validate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `crux mcp add` install packages and verify MCP servers work before registering them, so broken MCPs are caught immediately instead of at agent runtime.

**Architecture:** Replace the current write-only registration with install -> register -> probe -> rollback-on-failure for all MCP types. A new `install.py` module handles package installation and dependency detection. The existing `probe_mcp_server_detailed` in `health.py` gains a configurable timeout. `package_validation.py` is deleted.

**Tech Stack:** Python 3.11+, subprocess (npm, uv, git), existing `health.py` probe infrastructure.

---

### Task 1: Add configurable timeout to `probe_mcp_server_detailed`

**Files:**
- Modify: `src/crux_cli/health.py:26` — add `timeout` parameter
- Modify: `tests/unit/test_health.py` — add timeout test

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_health.py` at the end of `class TestProbeMcpServer`:

```python
def test_custom_timeout_passed_to_communicate(self, mocker):
    mocker.patch("crux_cli.health.shutil.which", return_value="/usr/bin/npx")
    mock_popen = mocker.patch("crux_cli.health.subprocess.Popen")
    mock_popen.return_value = _make_proc([INIT_RESPONSE, TOOLS_LIST_RESPONSE])
    h.probe_mcp_server_detailed({"command": "npx", "args": []}, timeout=45)
    mock_popen.return_value.communicate.assert_called_once()
    call_kwargs = mock_popen.return_value.communicate.call_args
    assert call_kwargs[1]["timeout"] == 45
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_health.py::TestProbeMcpServer::test_custom_timeout_passed_to_communicate -v`
Expected: FAIL — `probe_mcp_server_detailed` doesn't accept `timeout` parameter.

- [ ] **Step 3: Implement configurable timeout**

In `src/crux_cli/health.py`, change the function signatures:

```python
def probe_mcp_server(config: dict[str, Any], timeout: int = 10) -> tuple[str, str]:
    """Probe an MCP server via MCP initialize + tools/list handshake.
    Returns (status, reason).
    """
    result = probe_mcp_server_detailed(config, timeout=timeout)
    return result["status"], result["detail"]


def probe_mcp_server_detailed(config: dict[str, Any], timeout: int = 10) -> dict[str, Any]:
```

And change the hardcoded `timeout=10` in the `proc.communicate` call on line 88 to use the parameter:

```python
        stdout, _ = proc.communicate(input=messages.encode(), timeout=timeout)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_health.py -v`
Expected: All tests PASS (including the new one).

- [ ] **Step 5: Commit**

```bash
git add src/crux_cli/health.py tests/unit/test_health.py
git commit -m "feat: add configurable timeout to probe_mcp_server_detailed"
```

---

### Task 2: Create `install.py` with npm, uv, and dependency installation functions

**Files:**
- Create: `src/crux_cli/install.py`
- Create: `tests/unit/test_install.py`

- [ ] **Step 1: Write failing tests for `install_npm_package`**

Create `tests/unit/test_install.py`:

```python
"""Unit tests for crux_cli.install — all subprocess calls mocked."""

import subprocess
from unittest.mock import MagicMock

from crux_cli.install import install_npm_package


class TestInstallNpmPackage:
    def test_successful_install(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="added 1 package\n", stderr=""),
        )
        ok, err = install_npm_package("@test/mcp-server")
        assert ok
        assert err == ""

    def test_package_not_found(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="npm error E404 Not Found"),
        )
        ok, err = install_npm_package("nonexistent-pkg")
        assert not ok
        assert "not found" in err

    def test_install_failure_reported(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="ERR! engine incompatible"),
        )
        ok, err = install_npm_package("bad-pkg")
        assert not ok
        assert "npm install failed" in err

    def test_npm_not_installed_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=FileNotFoundError("npm not found"),
        )
        ok, err = install_npm_package("any-pkg")
        assert ok  # graceful skip

    def test_timeout_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="npm", timeout=120),
        )
        ok, err = install_npm_package("any-pkg")
        assert ok  # graceful skip
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_install.py::TestInstallNpmPackage -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement `install_npm_package`**

Create `src/crux_cli/install.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_install.py::TestInstallNpmPackage -v`
Expected: All PASS.

- [ ] **Step 5: Write failing tests for `install_uv_package`**

Append to `tests/unit/test_install.py`:

```python
from crux_cli.install import install_uv_package


class TestInstallUvPackage:
    def test_successful_install(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="Installed 1 package\n", stderr=""),
        )
        ok, err = install_uv_package("my-mcp-tool")
        assert ok
        assert err == ""

    def test_package_not_found(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(
                returncode=1, stdout="", stderr="error: Package `fake-pkg` not found"
            ),
        )
        ok, err = install_uv_package("fake-pkg")
        assert not ok
        assert "not found" in err

    def test_yanked_versions(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(
                returncode=1, stdout="", stderr="No solution found: all versions yanked"
            ),
        )
        ok, err = install_uv_package("yanked-pkg")
        assert not ok
        assert "not installable" in err

    def test_build_failure(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(
                returncode=1, stdout="", stderr="error: Failed to build pglast"
            ),
        )
        ok, err = install_uv_package("broken-pkg")
        assert not ok
        assert "uv tool install failed" in err

    def test_uv_not_installed_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=FileNotFoundError("uv not found"),
        )
        ok, err = install_uv_package("any-pkg")
        assert ok

    def test_timeout_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="uv", timeout=120),
        )
        ok, err = install_uv_package("any-pkg")
        assert ok
```

- [ ] **Step 6: Implement `install_uv_package`**

Append to `src/crux_cli/install.py`:

```python
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
```

- [ ] **Step 7: Run all install tests**

Run: `uv run pytest tests/unit/test_install.py -v`
Expected: All PASS.

- [ ] **Step 8: Write failing tests for `detect_and_install_deps`**

Append to `tests/unit/test_install.py`:

```python
from crux_cli.install import detect_and_install_deps


class TestDetectAndInstallDeps:
    def test_npm_project_with_build(self, tmp_path, mocker):
        pkg_json = {"scripts": {"build": "tsc"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg_json))
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        # Should have run npm install, then npm run build
        commands = [call[0][0] for call in mock_run.call_args_list]
        assert any("npm" in str(c) and "install" in str(c) for c in commands)
        assert "build_cmd" in entry

    def test_npm_project_no_build(self, tmp_path, mocker):
        pkg_json = {"scripts": {"start": "node index.js"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg_json))
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [call[0][0] for call in mock_run.call_args_list]
        assert any("npm" in str(c) and "install" in str(c) for c in commands)
        assert "build_cmd" not in entry

    def test_pyproject_toml(self, tmp_path, mocker):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [call[0][0] for call in mock_run.call_args_list]
        assert any("uv" in str(c) and "sync" in str(c) for c in commands)

    def test_requirements_txt(self, tmp_path, mocker):
        (tmp_path / "requirements.txt").write_text("requests\n")
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [str(call[0][0]) for call in mock_run.call_args_list]
        assert any("uv" in c for c in commands)

    def test_no_project_files_skips(self, tmp_path):
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        assert err == ""

    def test_npm_install_failure(self, tmp_path, mocker):
        (tmp_path / "package.json").write_text("{}")
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="npm ERR! network error"),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert not ok
        assert "npm install failed" in err
```

Add `import json` at the top of the test file if not already there.

- [ ] **Step 9: Implement `detect_and_install_deps`**

Append to `src/crux_cli/install.py`:

```python
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
```

- [ ] **Step 10: Run all install tests**

Run: `uv run pytest tests/unit/test_install.py -v`
Expected: All PASS.

- [ ] **Step 11: Lint**

Run: `uv run ruff check src/crux_cli/install.py tests/unit/test_install.py`
Expected: All checks passed.

- [ ] **Step 12: Commit**

```bash
git add src/crux_cli/install.py tests/unit/test_install.py
git commit -m "feat: add install.py with npm, uv, and dep detection"
```

---

### Task 3: Add `rollback_mcp_add` helper

**Files:**
- Modify: `src/crux_cli/install.py` — add rollback function
- Modify: `tests/unit/test_install.py` — add rollback tests

- [ ] **Step 1: Write failing tests for rollback**

Append to `tests/unit/test_install.py`:

```python
from crux_cli.install import rollback_mcp_add


class TestRollbackMcpAdd:
    def test_rollback_removes_registry_entry(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(json.dumps({
            "version": "1.0.0",
            "mcp_definitions": {"test-mcp": {"type": "npm-package"}},
            "skill_definitions": {},
        }))
        rollback_mcp_add("test-mcp", {"type": "npm-package"})
        reg = json.loads(reg_path.read_text())
        assert "test-mcp" not in reg["mcp_definitions"]

    def test_rollback_deletes_source_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        source_dir = tmp_path / "mcps" / "test-mcp"
        source_dir.mkdir(parents=True)
        (source_dir / "index.js").write_text("// test")
        reg_path.write_text(json.dumps({
            "version": "1.0.0",
            "mcp_definitions": {"test-mcp": {
                "type": "github", "source_dir": str(source_dir),
            }},
            "skill_definitions": {},
        }))
        rollback_mcp_add("test-mcp", {"type": "github", "source_dir": str(source_dir)})
        assert not source_dir.exists()

    def test_rollback_uvx_uninstalls(self, tmp_path, monkeypatch, mocker):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(json.dumps({
            "version": "1.0.0",
            "mcp_definitions": {"test-mcp": {
                "type": "uvx-package", "args": ["my-tool"],
            }},
            "skill_definitions": {},
        }))
        mock_run = mocker.patch("crux_cli.install.subprocess.run")
        rollback_mcp_add("test-mcp", {"type": "uvx-package", "args": ["my-tool"]})
        mock_run.assert_called_once()
        assert "uninstall" in str(mock_run.call_args)

    def test_rollback_npm_uninstalls(self, tmp_path, monkeypatch, mocker):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(json.dumps({
            "version": "1.0.0",
            "mcp_definitions": {"test-mcp": {
                "type": "npm-package", "args": ["-y", "@test/pkg"],
            }},
            "skill_definitions": {},
        }))
        mock_run = mocker.patch("crux_cli.install.subprocess.run")
        rollback_mcp_add("test-mcp", {"type": "npm-package", "args": ["-y", "@test/pkg"]})
        mock_run.assert_called_once()
        assert "uninstall" in str(mock_run.call_args)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_install.py::TestRollbackMcpAdd -v`
Expected: FAIL — `rollback_mcp_add` not defined.

- [ ] **Step 3: Implement `rollback_mcp_add`**

Append to `src/crux_cli/install.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_install.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crux_cli/install.py tests/unit/test_install.py
git commit -m "feat: add rollback_mcp_add helper"
```

---

### Task 4: Rewrite `cmd_mcp_add` to use install + probe + rollback

**Files:**
- Modify: `src/crux_cli/cli/commands/mcp.py` — rewrite `cmd_mcp_add`, delete `detect_and_run_build`
- Delete: `src/crux_cli/package_validation.py`
- Delete: `tests/unit/test_package_validation.py`

- [ ] **Step 1: Delete `package_validation.py` and its tests**

```bash
rm src/crux_cli/package_validation.py tests/unit/test_package_validation.py
```

- [ ] **Step 2: Rewrite `cmd_mcp_add` in `mcp.py`**

Replace the imports at the top of `src/crux_cli/cli/commands/mcp.py`. Remove:
```python
from crux_cli.package_validation import validate_npm_package, validate_pypi_package
```

Replace with:
```python
from crux_cli.install import (
    detect_and_install_deps,
    install_npm_package,
    install_uv_package,
    rollback_mcp_add,
)
```

Delete the `detect_and_run_build` function entirely (lines 28-42).

Replace the body of `cmd_mcp_add` from `skip_validation = ...` through `save_registry(reg)` / `print("Registered...")` with:

```python
    skip_validation = getattr(args, "skip_validation", False)

    if args.uv:
        if not skip_validation:
            print(f"  Installing {args.uv} via uv tool install...")
            ok, err = install_uv_package(args.uv)
            if not ok:
                print(f"\u274c Installation failed for '{args.uv}': {err}")
                print("  Use --skip-validation to register anyway.")
                sys.exit(1)
        base_args = [args.uv]
        if args.args:
            base_args += args.args.split()
        entry.update({"type": "uvx-package", "command": "uvx", "args": base_args})
    elif args.npm:
        if not skip_validation:
            print(f"  Installing {args.npm} via npm install -g...")
            ok, err = install_npm_package(args.npm)
            if not ok:
                print(f"\u274c Installation failed for '{args.npm}': {err}")
                print("  Use --skip-validation to register anyway.")
                sys.exit(1)
        base_args = ["-y", args.npm]
        if args.args:
            base_args += args.args.split()
        entry.update({"type": "npm-package", "command": "npx", "args": base_args})
    elif args.github:
        dest = v1_mcps_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Cloning: {args.github} -> {dest}")
        subprocess.run(  # noqa: S603
            ["git", "clone", f"https://github.com/{args.github}", str(dest)],  # noqa: S607
            check=True,
        )
        entry.update({"type": "github", "source": args.github, "source_dir": str(dest)})
        if args.command:
            run_args = args.args.split() if args.args else []
            entry.update({"command": args.command, "args": run_args})
        if not skip_validation:
            ok, err = detect_and_install_deps(dest, entry)
            if not ok:
                shutil.rmtree(dest, ignore_errors=True)
                print(f"\u274c Dependency installation failed: {err}")
                sys.exit(1)
    elif args.local:
        source = Path(args.local).resolve()
        dest = v1_mcps_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        entry.update({"type": "local", "source_dir": str(dest)})
        if args.command:
            entry.update({"command": args.command, "args": args.args.split() if args.args else []})
        if not skip_validation:
            ok, err = detect_and_install_deps(dest, entry)
            if not ok:
                shutil.rmtree(dest, ignore_errors=True)
                print(f"\u274c Dependency installation failed: {err}")
                sys.exit(1)
    else:
        print("\u274c Specify a source: --uv <package>, --npm <package>, --github <user/repo>, or --local <path>")
        sys.exit(1)

    reg[registry_key][name] = entry
    save_registry(reg)

    # Probe: verify the MCP server starts and responds
    if not skip_validation and entry.get("command"):
        from crux_cli.health import probe_mcp_server_detailed

        print("  Probing MCP server...")
        config = {"command": entry.get("command", ""), "args": entry.get("args", [])}
        if entry.get("env"):
            config["env"] = entry["env"]
        result = probe_mcp_server_detailed(config, timeout=60)
        if result["status"] == "failed":
            print(f"\u274c MCP server probe failed: {result['detail']}")
            rollback_mcp_add(name, entry)
            print("  Registration rolled back.")
            sys.exit(1)
        elif result["status"] == "connected":
            tools = result.get("tools_count")
            detail = result.get("detail", "")
            tools_str = f" ({tools} tools)" if tools is not None else ""
            print(f"  \u2705 Server verified: {detail}{tools_str}")
        else:
            print(f"  \u26a0\ufe0f  Server responded with status: {result['status']}")

    print(f"\u2705 Registered MCP '{name}'")
```

- [ ] **Step 3: Run lint**

Run: `uv run ruff check src/crux_cli/cli/commands/mcp.py`
Expected: All checks passed (or only pre-existing noqa issues).

- [ ] **Step 4: Run the full test suite**

Run: `uv run pytest tests/ -v --ignore=tests/integration/test_e2e_auth.py -x`
Expected: All tests PASS. The integration tests use `--skip-validation` so they bypass the new install logic.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: rewrite cmd_mcp_add with install + probe + rollback (closes #27, closes #28)"
```

---

### Task 5: Update integration tests for install + probe behavior

**Files:**
- Modify: `tests/integration/test_cli_mcp.py` — add tests for validation behavior

- [ ] **Step 1: Add test that --skip-validation bypasses install**

Append to `TestMcpAdd` in `tests/integration/test_cli_mcp.py`:

```python
    def test_add_skip_validation_registers_without_install(self, crux_env):
        """--skip-validation should register even with a fake package."""
        env, root = crux_env
        result = run_crux(
            "mcp",
            "add",
            "fake-npm",
            "--npm",
            "totally-fake-nonexistent-pkg-xyz",
            "--skip-validation",
            env=env,
        )
        assert result.returncode == 0
        assert "Registered MCP" in result.stdout
        reg = _load_registry(root)
        assert "fake-npm" in reg["mcp_definitions"]

    def test_add_skip_validation_uv(self, crux_env):
        """--skip-validation for --uv should also work."""
        env, root = crux_env
        result = run_crux(
            "mcp",
            "add",
            "fake-uv",
            "--uv",
            "totally-fake-nonexistent-pkg-xyz",
            "--skip-validation",
            env=env,
        )
        assert result.returncode == 0
        reg = _load_registry(root)
        assert "fake-uv" in reg["mcp_definitions"]
```

- [ ] **Step 2: Run the new tests**

Run: `uv run pytest tests/integration/test_cli_mcp.py -v`
Expected: All PASS.

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/integration/test_e2e_auth.py -x`
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_cli_mcp.py
git commit -m "test: add integration tests for skip-validation behavior"
```

---

### Task 6: Final cleanup and full verification

**Files:**
- Verify all tests pass
- Verify lint passes
- Verify no stale references to `package_validation`

- [ ] **Step 1: Check for stale references**

Run: `grep -r "package_validation" src/ tests/`
Expected: No results.

- [ ] **Step 2: Full lint**

Run: `uv run ruff check src/ tests/`
Expected: All checks passed.

- [ ] **Step 3: Full test suite**

Run: `uv run pytest tests/ -v --ignore=tests/integration/test_e2e_auth.py`
Expected: All tests PASS.

- [ ] **Step 4: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: final cleanup for mcp add install and validate"
```
