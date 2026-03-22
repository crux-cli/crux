"""Unit tests for crux_cli.sync — sync engine and .mcp.json generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crux_cli.sync import (
    _build_http_bridge_entry,
    _build_keychain_auth_entry,
    _build_server_entry,
    sync_project,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry(mcps=None, skills=None):
    """Build a minimal registry dict."""
    return {
        "version": "1.0.0",
        "mcp_definitions": mcps or {},
        "skill_definitions": skills or {},
    }


def _make_crux_json(project_dir, name="test-project", mcps=None, skills=None):
    """Write a crux.json into project_dir and return the dict."""
    data = {"name": name, "mcps": mcps or [], "skills": skills or []}
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "crux.json").write_text(json.dumps(data, indent=2))
    return data


# ---------------------------------------------------------------------------
# sync_project
# ---------------------------------------------------------------------------


class TestSyncGeneratesMcpJson:
    def test_sync_generates_mcp_json(self, tmp_path):
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["memory"])
        registry = _make_registry(
            mcps={
                "memory": {
                    "type": "npm-package",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                }
            }
        )

        success, issues = sync_project(project, registry)
        assert success
        assert issues == []

        mcp_json = project / ".mcp.json"
        assert mcp_json.exists()
        data = json.loads(mcp_json.read_text())
        assert "mcpServers" in data
        assert "memory" in data["mcpServers"]

    def test_sync_mcp_json_format_valid(self, tmp_path):
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["memory"])
        registry = _make_registry(
            mcps={
                "memory": {"command": "npx", "args": ["-y", "pkg"]},
            }
        )

        sync_project(project, registry)
        data = json.loads((project / ".mcp.json").read_text())

        # Must have the Claude Code format: {"mcpServers": {...}}
        assert isinstance(data, dict)
        assert "mcpServers" in data
        server = data["mcpServers"]["memory"]
        assert "command" in server

    def test_sync_missing_mcp_errors(self, tmp_path):
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["nonexistent"])
        registry = _make_registry()

        success, issues = sync_project(project, registry)
        assert success  # sync still writes .mcp.json
        assert any("nonexistent" in i and "not found" in i for i in issues)

    def test_sync_empty_mcps(self, tmp_path):
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=[])
        registry = _make_registry()

        success, issues = sync_project(project, registry)
        assert success
        assert issues == []
        data = json.loads((project / ".mcp.json").read_text())
        assert data["mcpServers"] == {}


class TestSyncAuthedMcpUsesSharedLauncher:
    """Authed MCPs reference the shared keychain-auth.sh via env config."""

    def test_sync_authed_mcp_uses_shared_launcher(self, tmp_path):
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["authed-mcp"])
        registry = _make_registry(
            mcps={
                "authed-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-pkg"],
                    "auth": {"env_vars": ["API_KEY"]},
                }
            }
        )

        sync_project(project, registry)

        data = json.loads((project / ".mcp.json").read_text())
        server = data["mcpServers"]["authed-mcp"]
        assert server["command"].endswith("keychain-auth.sh")
        assert server["env"]["CRUX_MCP_NAME"] == "authed-mcp"
        assert server["env"]["CRUX_AUTH_ENV_VARS"] == "API_KEY"
        # The actual MCP command is passed as args to the shared launcher
        assert "npx" in server["args"]

    def test_sync_no_launcher_files_generated(self, tmp_path):
        """No per-MCP .sh files should be generated anywhere."""
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["authed-mcp"])
        registry = _make_registry(
            mcps={
                "authed-mcp": {
                    "command": "npx",
                    "args": ["-y", "pkg"],
                    "auth": {"env_vars": ["SECRET"]},
                }
            }
        )

        sync_project(project, registry)

        # No .sh files should exist in the project or temp directory
        sh_files = list(tmp_path.rglob("authed-mcp.sh"))
        assert sh_files == []


class TestSyncAllTrackedProjects:
    def test_sync_all_tracked_projects(self, tmp_path):
        """Verify sync_project works on multiple project dirs."""
        registry = _make_registry(
            mcps={
                "memory": {"command": "npx", "args": ["-y", "pkg"]},
            }
        )

        projects = []
        for name in ("proj-a", "proj-b"):
            p = tmp_path / name
            _make_crux_json(p, name=name, mcps=["memory"])
            projects.append(p)

        for p in projects:
            success, issues = sync_project(p, registry)
            assert success
            assert issues == []
            assert (p / ".mcp.json").exists()


# ---------------------------------------------------------------------------
# _build_keychain_auth_entry
# ---------------------------------------------------------------------------


class TestKeychainAuthEntry:
    """Tests for the shared keychain launcher entry builder."""

    def test_entry_structure(self):
        mcp_data = {
            "command": "npx",
            "args": ["-y", "some-pkg"],
            "auth": {"env_vars": ["API_KEY", "SECRET_TOKEN"]},
        }
        entry = _build_keychain_auth_entry("test-mcp", mcp_data)

        assert entry["command"].endswith("keychain-auth.sh")
        assert entry["env"]["CRUX_MCP_NAME"] == "test-mcp"
        assert entry["env"]["CRUX_AUTH_ENV_VARS"] == "API_KEY,SECRET_TOKEN"
        # MCP command + original args are passed as positional args
        assert entry["args"][0] == "npx"
        assert "-y" in entry["args"]
        assert "some-pkg" in entry["args"]

    def test_extra_args_appended(self):
        mcp_data = {
            "command": "npx",
            "args": ["-y", "pkg"],
            "auth": {"env_vars": ["K"]},
        }
        entry = _build_keychain_auth_entry("test-mcp", mcp_data, extra_args=["--port", "8080"])

        assert entry["args"][-2:] == ["--port", "8080"]

    def test_source_dir_resolved_to_absolute(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / ".crux"))
        mcp_data = {
            "command": "uv",
            "args": ["run", "--directory", "{source_dir}", "serve"],
            "source_dir": "mcps/my-mcp",
            "auth": {"env_vars": ["K"]},
        }
        entry = _build_keychain_auth_entry("my-mcp", mcp_data)

        # {source_dir} should be resolved to an absolute path
        assert "{source_dir}" not in str(entry["args"])
        dir_arg = entry["args"][3]  # uv, run, --directory, <path>
        assert Path(dir_arg).is_absolute()

    def test_rejects_unsafe_mcp_name(self):
        mcp_data = {"command": "npx", "args": [], "auth": {"env_vars": ["K"]}}
        with pytest.raises(ValueError, match="Unsafe MCP name"):
            _build_keychain_auth_entry("../evil", mcp_data)

    def test_rejects_unsafe_env_var(self):
        mcp_data = {"command": "npx", "args": [], "auth": {"env_vars": ["BAD VAR"]}}
        with pytest.raises(ValueError, match="Unsafe env var"):
            _build_keychain_auth_entry("test-mcp", mcp_data)


# ---------------------------------------------------------------------------
# _build_http_bridge_entry
# ---------------------------------------------------------------------------


class TestHttpBridgeEntry:
    """Tests for HTTP bridge entry builder."""

    def test_bearer_entry_structure(self):
        mcp_data = {
            "type": "streamable-http",
            "url": "https://example.com/mcp",
            "auth": {
                "type": "bearer",
                "keychain_key": "API_TOKEN",
                "header_name": "Authorization",
                "header_prefix": "Bearer",
            },
        }
        entry = _build_http_bridge_entry("test-mcp", mcp_data)

        assert entry["command"].endswith("http-bridge-auth.sh")
        assert entry["args"] == []
        assert entry["env"]["CRUX_MCP_NAME"] == "test-mcp"
        assert entry["env"]["CRUX_BRIDGE_URL"] == "https://example.com/mcp"
        assert entry["env"]["CRUX_BRIDGE_AUTH_HEADER"] == "Authorization"
        assert entry["env"]["CRUX_BRIDGE_AUTH_PREFIX"] == "Bearer"
        assert entry["env"]["CRUX_AUTH_KEYCHAIN_KEY"] == "API_TOKEN"
        assert entry["env"]["CRUX_BRIDGE_AUTH_ENV"] == "CRUX_AUTH_TOKEN"

    def test_oauth_uses_access_token_key(self):
        mcp_data = {
            "type": "streamable-http",
            "url": "https://example.com/mcp",
            "auth": {"type": "oauth"},
        }
        entry = _build_http_bridge_entry("test-mcp", mcp_data)

        assert entry["env"]["CRUX_AUTH_KEYCHAIN_KEY"] == "access_token"

    def test_oauth_client_credentials_uses_access_token_key(self):
        mcp_data = {
            "type": "streamable-http",
            "url": "https://example.com/mcp",
            "auth": {"type": "oauth-client-credentials"},
        }
        entry = _build_http_bridge_entry("test-mcp", mcp_data)

        assert entry["env"]["CRUX_AUTH_KEYCHAIN_KEY"] == "access_token"

    def test_no_auth_bridge_entry(self):
        """HTTP MCP with no auth still gets bridge env vars."""
        mcp_data = {
            "type": "streamable-http",
            "url": "https://example.com/mcp",
            "auth": {},
        }
        entry = _build_http_bridge_entry("test-mcp", mcp_data)

        assert entry["env"]["CRUX_BRIDGE_URL"] == "https://example.com/mcp"
        assert "CRUX_AUTH_KEYCHAIN_KEY" not in entry["env"]


# ---------------------------------------------------------------------------
# _build_server_entry dispatch
# ---------------------------------------------------------------------------


class TestBuildServerEntryDispatch:
    """Verify _build_server_entry routes to the correct builder."""

    def test_http_mcp_routes_to_bridge(self):
        mcp_data = {
            "type": "streamable-http",
            "url": "https://example.com/mcp",
            "auth": {"type": "bearer", "keychain_key": "TOK"},
        }
        entry = _build_server_entry("test-mcp", mcp_data)
        assert entry["command"].endswith("http-bridge-auth.sh")

    def test_url_field_routes_to_bridge(self):
        mcp_data = {"url": "https://example.com/mcp", "auth": {}}
        entry = _build_server_entry("test-mcp", mcp_data)
        assert entry["command"].endswith("http-bridge-auth.sh")

    def test_authed_stdio_routes_to_keychain(self):
        mcp_data = {
            "command": "npx",
            "args": ["-y", "pkg"],
            "auth": {"env_vars": ["API_KEY"]},
        }
        entry = _build_server_entry("test-mcp", mcp_data)
        assert entry["command"].endswith("keychain-auth.sh")

    def test_plain_mcp_passthrough(self):
        mcp_data = {"command": "npx", "args": ["-y", "pkg"]}
        entry = _build_server_entry("test-mcp", mcp_data)
        assert entry["command"] == "npx"
        assert entry["args"] == ["-y", "pkg"]

    def test_plain_mcp_with_extra_args(self):
        mcp_data = {"command": "npx", "args": ["-y", "pkg"]}
        entry = _build_server_entry("test-mcp", mcp_data, extra_args=["--port", "8080"])
        assert entry["args"] == ["-y", "pkg", "--port", "8080"]

    def test_plain_mcp_resolves_source_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / ".crux"))
        mcp_data = {
            "command": "uv",
            "args": ["run", "--directory", "{source_dir}", "serve"],
            "source_dir": "mcps/my-mcp",
        }
        entry = _build_server_entry("my-mcp", mcp_data)
        assert "{source_dir}" not in str(entry["args"])
        assert Path(entry["args"][2]).is_absolute()


# ---------------------------------------------------------------------------
# Shared launcher scripts exist as package data
# ---------------------------------------------------------------------------


class TestSharedLauncherScriptsExist:
    """Verify the bundled shared launcher scripts are present in the package."""

    def test_keychain_auth_script_exists(self):
        from crux_cli.setup_crux import _BUNDLED_LAUNCHERS

        script = _BUNDLED_LAUNCHERS / "keychain-auth.sh"
        assert script.exists(), f"Bundled script not found at {script}"
        content = script.read_text()
        assert "CRUX_MCP_NAME" in content
        assert "CRUX_AUTH_ENV_VARS" in content
        assert "uname -s" in content  # platform detection

    def test_http_bridge_auth_script_exists(self):
        from crux_cli.setup_crux import _BUNDLED_LAUNCHERS

        script = _BUNDLED_LAUNCHERS / "http-bridge-auth.sh"
        assert script.exists(), f"Bundled script not found at {script}"
        content = script.read_text()
        assert "CRUX_MCP_NAME" in content
        assert "CRUX_AUTH_KEYCHAIN_KEY" in content
        assert "crux_cli.bridge" in content

    def test_scripts_have_both_platform_branches(self):
        """Both scripts must handle macOS (security) and Linux (secret-tool)."""
        from crux_cli.setup_crux import _BUNDLED_LAUNCHERS

        for name in ("keychain-auth.sh", "http-bridge-auth.sh"):
            content = (_BUNDLED_LAUNCHERS / name).read_text()
            assert "Darwin" in content, f"{name} missing macOS branch"
            assert "security find-generic-password" in content, f"{name} missing macOS command"
            assert "secret-tool lookup" in content, f"{name} missing Linux command"
