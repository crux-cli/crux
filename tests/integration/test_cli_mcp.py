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
        result = run_crux(
            "mcp",
            "add",
            "new-mcp",
            "--npm",
            "@test/new-mcp",
            "--tags",
            "test",
            "--skip-validation",
            env=env,
        )
        assert result.returncode == 0
        assert "Registered MCP" in result.stdout
        reg = _load_registry(root)
        assert "new-mcp" in reg["mcp_definitions"]

    def test_add_duplicate_fails(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "dup", "--npm", "@test/dup", "--skip-validation", env=env)
        result = run_crux("mcp", "add", "dup", "--npm", "@test/dup", "--skip-validation", env=env)
        assert result.returncode != 0
        assert "already exists" in result.stdout

    def test_add_no_source_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "add", "nosrc", env=env)
        assert result.returncode != 0

    def test_add_setup_cmd_rejected(self, crux_env):
        """--setup-cmd is no longer a valid flag."""
        env, root = crux_env
        result = run_crux("mcp", "add", "x", "--npm", "pkg", "--setup-cmd", "echo hi", env=env)
        assert result.returncode != 0  # argparse rejects unknown argument

    def test_add_with_keychain_registers_auth(self, crux_env):
        """--keychain stores auth metadata in registry even without interactive prompt."""
        env, root = crux_env
        result = run_crux(
            "mcp",
            "add",
            "authed",
            "--npm",
            "@test/authed",
            "--keychain",
            "API_KEY,SECRET",
            "--skip-validation",
            env=env,
        )
        assert result.returncode == 0
        reg = _load_registry(root)
        auth = reg["mcp_definitions"]["authed"].get("auth", {})
        assert auth["type"] == "keychain"
        assert auth["env_vars"] == ["API_KEY", "SECRET"]

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


@pytest.mark.integration
class TestMcpRemove:
    def test_remove_existing(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "to-remove", "--npm", "@test/pkg", "--skip-validation", env=env)
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
        run_crux(
            "mcp",
            "add",
            "authed",
            "--npm",
            "@test/authed",
            "--keychain",
            "KEY1,KEY2",
            "--skip-validation",
            env=env,
        )
        result = run_crux("mcp", "remove", "authed", "--keep-secrets", env=env)
        assert result.returncode == 0
        assert "Removed" in result.stdout

    def test_remove_with_remove_secrets_flag(self, crux_env):
        env, root = crux_env
        run_crux(
            "mcp",
            "add",
            "authed2",
            "--npm",
            "@test/authed2",
            "--keychain",
            "KEY1",
            "--skip-validation",
            env=env,
        )
        result = run_crux("mcp", "remove", "authed2", "--remove-secrets", env=env)
        assert result.returncode == 0
        assert "Removed" in result.stdout

    def test_remove_secrets_flags_mutually_exclusive(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "remove", "x", "--keep-secrets", "--remove-secrets", env=env)
        assert result.returncode != 0


@pytest.mark.integration
class TestMcpAuth:
    def test_auth_value_flag_accepted(self, crux_env):
        """--value flag is accepted by the CLI parser."""
        env, root = crux_env
        run_crux(
            "mcp",
            "add",
            "authed",
            "--npm",
            "@test/authed",
            "--keychain",
            "API_KEY",
            "--skip-validation",
            env=env,
        )
        # --value should be accepted (may fail to store due to keychain, but shouldn't be a parse error)
        result = run_crux("mcp", "auth", "authed", "--value", "API_KEY=test123", env=env)
        # Should not fail with argparse error (exit code 2)
        assert result.returncode != 2

    def test_auth_value_invalid_format_fails(self, crux_env):
        """--value without = should fail."""
        env, root = crux_env
        run_crux(
            "mcp",
            "add",
            "authed2",
            "--npm",
            "@test/authed2",
            "--keychain",
            "KEY",
            "--skip-validation",
            env=env,
        )
        result = run_crux("mcp", "auth", "authed2", "--value", "NOEQUALS", env=env)
        assert result.returncode != 0
        assert "Invalid --value format" in result.stdout


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
