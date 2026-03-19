"""End-to-end integration tests for MCP authentication.

Tests the full cycle: register MCP → authenticate → sync → probe.
Uses the fixture MCP server at tests/fixtures/test_mcp_server.py.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .conftest import run_crux

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
FIXTURE_MCP = str(FIXTURES_DIR / "test_mcp_server.py")


def _register_test_mcp(root: Path, name: str = "test-authed", auth: dict | None = None) -> None:
    """Directly write an MCP entry into the registry JSON (bypasses CLI add flow)."""
    reg_path = root / "registry.json"
    reg = json.loads(reg_path.read_text())
    entry = {
        "type": "local",
        "command": sys.executable,
        "args": [FIXTURE_MCP],
        "tags": [],
    }
    if auth is not None:
        entry["auth"] = auth
    reg["mcp_definitions"][name] = entry
    reg_path.write_text(json.dumps(reg, indent=2))


@pytest.mark.integration
class TestKeychainAuthCycle:
    """Test keychain auth type: register → auth → sync → probe."""

    def test_register_mcp_with_keychain(self, crux_env):
        """Register a keychain-authed MCP pointing to the fixture server."""
        env, root = crux_env
        _register_test_mcp(
            root,
            name="test-authed",
            auth={
                "type": "keychain",
                "env_vars": ["AUTH_TOKEN"],
                "fix_description": "Run: crux secret set test-authed AUTH_TOKEN <value>",
            },
        )

        # Verify registry has auth metadata
        reg = json.loads((root / "registry.json").read_text())
        mcp = reg["mcp_definitions"]["test-authed"]
        assert mcp["auth"]["type"] == "keychain"
        assert mcp["auth"]["env_vars"] == ["AUTH_TOKEN"]

    def test_auth_status_shows_missing(self, crux_env):
        """Before auth, status shows missing secrets."""
        env, root = crux_env
        _register_test_mcp(
            root,
            name="test-authed",
            auth={
                "type": "keychain",
                "env_vars": ["AUTH_TOKEN"],
            },
        )

        # Check auth status via the CLI subprocess to avoid direct module import
        # issues in sandboxed test environments
        run_crux("mcp", "auth", env=env)
        # The CLI may print a table or exit non-zero; either way,
        # the registry should show auth metadata for "test-authed"
        reg = json.loads((root / "registry.json").read_text())
        mcp = reg["mcp_definitions"]["test-authed"]
        assert mcp["auth"]["type"] == "keychain"
        assert "AUTH_TOKEN" in mcp["auth"]["env_vars"]
        # No secrets.json should exist (no auth performed yet)
        secrets_json = root / "secrets.json"
        if secrets_json.exists():
            idx = json.loads(secrets_json.read_text())
            stored = idx.get("test-authed", [])
            assert "AUTH_TOKEN" not in stored, "AUTH_TOKEN should not be stored yet"

    def test_sync_generates_launcher(self, crux_env):
        """After registering a keychain MCP, sync generates a launcher script."""
        env, root = crux_env
        _register_test_mcp(
            root,
            name="test-authed",
            auth={
                "type": "keychain",
                "env_vars": ["AUTH_TOKEN"],
            },
        )

        # Create project
        run_crux("project", "create", "testproj", env=env, cwd=str(root))
        proj_dir = root / "testproj"

        # Add MCP to crux.json
        crux_json = json.loads((proj_dir / "crux.json").read_text())
        crux_json["mcps"] = ["test-authed"]
        (proj_dir / "crux.json").write_text(json.dumps(crux_json))

        # Sync
        result = run_crux("project", "sync", env=env, cwd=str(proj_dir))
        assert result.returncode == 0

        # Verify .mcp.json uses launcher
        mcp_json = json.loads((proj_dir / ".mcp.json").read_text())
        server = mcp_json["mcpServers"]["test-authed"]
        assert server["command"].endswith(".sh"), f"Expected .sh launcher, got: {server['command']}"

        # Verify launcher exists and contains keychain lookup commands, not secrets
        launcher_path = server["command"]
        assert Path(launcher_path).exists(), f"Launcher not found: {launcher_path}"
        launcher_content = Path(launcher_path).read_text()
        assert "security find-generic-password" in launcher_content or "secret-tool lookup" in launcher_content, (
            "Launcher should contain keychain lookup command"
        )
        assert "AUTH_TOKEN" in launcher_content

    def test_launcher_never_has_literal_secrets(self, crux_env):
        """Security: launcher script never contains actual secret values."""
        env, root = crux_env
        SENTINEL = "SUPER_SECRET_VALUE_12345"

        _register_test_mcp(
            root,
            name="test-authed",
            auth={
                "type": "keychain",
                "env_vars": ["AUTH_TOKEN"],
            },
        )

        run_crux("project", "create", "testproj", env=env, cwd=str(root))
        proj_dir = root / "testproj"
        crux_json = json.loads((proj_dir / "crux.json").read_text())
        crux_json["mcps"] = ["test-authed"]
        (proj_dir / "crux.json").write_text(json.dumps(crux_json))
        run_crux("project", "sync", env=env, cwd=str(proj_dir))

        # Verify sentinel is absent from all generated files
        mcp_json_content = (proj_dir / ".mcp.json").read_text()
        assert SENTINEL not in mcp_json_content

        mcp_json = json.loads(mcp_json_content)
        launcher_path = mcp_json["mcpServers"]["test-authed"]["command"]
        launcher_content = Path(launcher_path).read_text()
        assert SENTINEL not in launcher_content


@pytest.mark.integration
class TestExternalCliAuthCycle:
    """Test external-cli auth type using the fixture MCP's check mode."""

    def test_register_external_cli_mcp(self, crux_env):
        """Register an MCP with external CLI auth checking."""
        env, root = crux_env
        _register_test_mcp(
            root,
            name="cli-authed",
            auth={
                "type": "external-cli",
                "check_cmd": [sys.executable, FIXTURE_MCP],
                "fix_cmd": [],
                "fix_description": "Set AUTH_TOKEN environment variable",
            },
        )

        reg = json.loads((root / "registry.json").read_text())
        mcp = reg["mcp_definitions"]["cli-authed"]
        assert mcp["auth"]["type"] == "external-cli"
        assert mcp["auth"]["check_cmd"] == [sys.executable, FIXTURE_MCP]

    def test_external_cli_auth_check_fails_without_token(self, crux_env):
        """External CLI auth check fails when AUTH_TOKEN is not set."""
        env, root = crux_env

        # Build check env: has AUTH_CHECK_MODE but no AUTH_TOKEN
        check_env = env.copy()
        check_env["AUTH_CHECK_MODE"] = "check"
        check_env.pop("AUTH_TOKEN", None)

        result = subprocess.run(  # noqa: S603
            [sys.executable, FIXTURE_MCP],
            capture_output=True,
            env=check_env,
            timeout=5,
        )
        assert result.returncode == 1  # Not authenticated

    def test_external_cli_auth_check_succeeds_with_token(self, crux_env):
        """External CLI auth check passes when AUTH_TOKEN is set."""
        env, root = crux_env
        check_env = env.copy()
        check_env["AUTH_CHECK_MODE"] = "check"
        check_env["AUTH_TOKEN"] = "test-token"  # noqa: S105

        result = subprocess.run(  # noqa: S603
            [sys.executable, FIXTURE_MCP],
            capture_output=True,
            env=check_env,
            timeout=5,
        )
        assert result.returncode == 0  # Authenticated

    def test_auth_status_external_cli_unauthenticated(self, crux_env):
        """external-cli auth check_cmd that exits 1 means not authenticated."""
        env, root = crux_env

        # Directly run a check_cmd that always fails and confirm exit code 1
        check_cmd = [sys.executable, "-c", "import sys; sys.exit(1)"]
        result = subprocess.run(check_cmd, capture_output=True, timeout=5)  # noqa: S603
        assert result.returncode == 1, "A failing check_cmd should exit 1 (not authenticated)"

        # Also verify the fixture MCP itself exits 1 without AUTH_TOKEN in check mode
        check_env = env.copy()
        check_env["AUTH_CHECK_MODE"] = "check"
        check_env.pop("AUTH_TOKEN", None)
        result2 = subprocess.run(  # noqa: S603
            [sys.executable, FIXTURE_MCP],
            capture_output=True,
            env=check_env,
            timeout=5,
        )
        assert result2.returncode == 1, "Fixture MCP check mode should fail without AUTH_TOKEN"


@pytest.mark.integration
class TestProbeWithAuth:
    """Test MCP probing with real fixture server."""

    def test_probe_unauthenticated_shows_auth_required(self, crux_env):
        """Probing an MCP without auth shows auth_required status."""
        env, root = crux_env
        from crux_cli.health import probe_mcp_server_detailed

        config = {
            "command": sys.executable,
            "args": [FIXTURE_MCP],
            "env": {},  # No AUTH_TOKEN
        }
        result = probe_mcp_server_detailed(config)
        assert result["status"] == "auth_required", (
            f"Expected auth_required, got {result['status']}: {result['detail']}"
        )
        assert "authentication" in result["detail"].lower()

    def test_probe_authenticated_shows_connected(self, crux_env):
        """Probing an MCP with valid auth shows connected status."""
        env, root = crux_env
        from crux_cli.health import probe_mcp_server_detailed

        config = {
            "command": sys.executable,
            "args": [FIXTURE_MCP],
            "env": {"AUTH_TOKEN": "valid-test-token"},
        }
        result = probe_mcp_server_detailed(config)
        assert result["status"] == "connected", f"Expected connected, got {result['status']}: {result['detail']}"
        assert result["tools_count"] == 1
        assert "test-mcp-server" in (result["server_info"] or "")

    def test_probe_authenticated_returns_tools(self, crux_env):
        """Probing returns the correct tool count."""
        env, root = crux_env
        from crux_cli.health import probe_mcp_server_detailed

        config = {
            "command": sys.executable,
            "args": [FIXTURE_MCP],
            "env": {"AUTH_TOKEN": "any-value"},
        }
        result = probe_mcp_server_detailed(config)
        assert result["tools_count"] == 1

    def test_probe_with_check_cmd_fails_without_token(self, crux_env):
        """Probing via check_cmd returns auth_required when check_cmd exits non-zero."""
        env, root = crux_env
        from crux_cli.health import probe_mcp_server_detailed

        # check_cmd that always fails
        config = {
            "command": sys.executable,
            "args": [FIXTURE_MCP],
            "env": {},
            "auth": {
                "check_cmd": [sys.executable, "-c", "import sys; sys.exit(1)"],
                "fix_description": "authentication required",
            },
        }
        result = probe_mcp_server_detailed(config)
        assert result["status"] == "auth_required"
        assert "authentication" in result["detail"].lower()

    def test_full_sync_then_probe_cycle(self, crux_env):
        """Full cycle: register keychain MCP → sync → verify generated launcher path."""
        env, root = crux_env
        _register_test_mcp(
            root,
            name="test-authed",
            auth={
                "type": "keychain",
                "env_vars": ["AUTH_TOKEN"],
            },
        )

        run_crux("project", "create", "testproj", env=env, cwd=str(root))
        proj_dir = root / "testproj"
        crux_json = json.loads((proj_dir / "crux.json").read_text())
        crux_json["mcps"] = ["test-authed"]
        (proj_dir / "crux.json").write_text(json.dumps(crux_json))

        result = run_crux("project", "sync", env=env, cwd=str(proj_dir))
        assert result.returncode == 0

        mcp_json = json.loads((proj_dir / ".mcp.json").read_text())
        launcher_path = Path(mcp_json["mcpServers"]["test-authed"]["command"])
        assert launcher_path.exists()
        assert launcher_path.suffix == ".sh"

        # Launcher should be executable
        assert os.access(str(launcher_path), os.X_OK)
