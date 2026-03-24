"""Integration tests: crux mcp add/remove/list"""

import json

import pytest

from .conftest import run_crux


def _load_registry(root):
    reg_path = root / "registry.json"
    with open(reg_path) as f:
        return json.load(f)


@pytest.mark.integration
class TestMcpAdd:
    def test_add_npx_mcp(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "add", "new-mcp", "--npx", "@test/new-mcp", "--tags", "test", env=env)
        assert result.returncode == 0
        assert "Registered MCP" in result.stdout
        reg = _load_registry(root)
        assert "new-mcp" in reg["mcp_definitions"]

    def test_add_duplicate_fails(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "dup", "--npx", "@test/dup", env=env)
        result = run_crux("mcp", "add", "dup", "--npx", "@test/dup", env=env)
        assert result.returncode != 0
        assert "already exists" in result.stdout

    def test_add_no_source_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "add", "nosrc", env=env)
        assert result.returncode != 0

    def test_add_setup_cmd_rejected(self, crux_env):
        """--setup-cmd is no longer a valid flag."""
        env, root = crux_env
        result = run_crux("mcp", "add", "x", "--npx", "pkg", "--setup-cmd", "echo hi", env=env)
        assert result.returncode != 0  # argparse rejects unknown argument

    def test_add_with_keychain_registers_auth(self, crux_env):
        """--keychain stores auth metadata in registry even without interactive prompt."""
        env, root = crux_env
        result = run_crux("mcp", "add", "authed", "--npx", "@test/authed", "--keychain", "API_KEY,SECRET", env=env)
        assert result.returncode == 0
        reg = _load_registry(root)
        auth = reg["mcp_definitions"]["authed"].get("auth", {})
        assert auth["type"] == "keychain"
        assert auth["env_vars"] == ["API_KEY", "SECRET"]


@pytest.mark.integration
class TestMcpRemove:
    def test_remove_existing(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "to-remove", "--npx", "@test/pkg", env=env)
        result = run_crux("mcp", "remove", "to-remove", env=env)
        assert result.returncode == 0
        assert "Removed" in result.stdout
        reg = _load_registry(root)
        assert "to-remove" not in reg["mcp_definitions"]

    def test_remove_nonexistent_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "remove", "nope", env=env)
        assert result.returncode != 0

    def test_remove_with_keep_secrets_flag(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "authed", "--npx", "@test/authed", "--keychain", "KEY1,KEY2", env=env)
        result = run_crux("mcp", "remove", "authed", "--keep-secrets", env=env)
        assert result.returncode == 0
        assert "Removed" in result.stdout

    def test_remove_with_remove_secrets_flag(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "authed2", "--npx", "@test/authed2", "--keychain", "KEY1", env=env)
        result = run_crux("mcp", "remove", "authed2", "--remove-secrets", env=env)
        assert result.returncode == 0
        assert "Removed" in result.stdout

    def test_remove_secrets_flags_mutually_exclusive(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "remove", "x", "--keep-secrets", "--remove-secrets", env=env)
        assert result.returncode != 0


@pytest.mark.integration
class TestMcpList:
    def test_list_shows_mcps(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "list", env=env)
        assert result.returncode == 0

    def test_list_json(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "list", "--json", env=env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "mcp_definitions" in data
