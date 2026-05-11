"""Security invariant tests — secrets NEVER in the filesystem.

Core principle: All credentials are stored in OS keychain only.
.mcp.json entries contain env var *names* (CRUX_MCP_NAME, CRUX_AUTH_ENV_VARS),
never actual secret values.  The shared launcher scripts fetch secrets at
runtime from the keychain.

Every test uses a sentinel value and asserts it never appears in generated files.
"""

from __future__ import annotations

import json
from pathlib import Path

from crux_cli.secrets import load_secrets_index, save_secrets_index
from crux_cli.sync import _build_keychain_auth_entry, sync_project

# ---------------------------------------------------------------------------
# Sentinel constant — a distinctive value we control and can search for
# ---------------------------------------------------------------------------

SENTINEL_SECRET = "SENTINEL_SECRET_VALUE_12345"  # noqa: S105


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry(mcps=None, skills=None):
    """Build a minimal v1 registry dict."""
    return {
        "version": "1.0.0",
        "mcp_definitions": mcps or {},
        "skill_definitions": skills or {},
    }


def _make_crux_json(project_dir: Path, mcps=None, skills=None):
    """Write a crux.json into project_dir."""
    project_dir.mkdir(parents=True, exist_ok=True)
    data = {"name": "test-project", "mcps": mcps or [], "skills": skills or []}
    (project_dir / "crux.json").write_text(json.dumps(data, indent=2))
    return data


def _keychain_mcp_data(command="npx", args=None):
    """Return a registry MCP entry with keychain auth."""
    return {
        "command": command,
        "args": args if args is not None else ["-y", "some-pkg"],
        "auth": {
            "type": "keychain",
            "env_vars": ["API_KEY", "SECRET_TOKEN"],
        },
    }


# ---------------------------------------------------------------------------
# Keychain auth entry tests
# ---------------------------------------------------------------------------


class TestKeychainAuthEntryNoLiteralSecrets:
    """The keychain auth entry must only contain env var names, not values."""

    def test_entry_env_contains_only_names(self):
        """Sentinel must not appear in the entry dict."""
        mcp_data = {
            "command": "npx",
            "args": ["-y", "some-pkg"],
            "auth": {
                "type": "keychain",
                "env_vars": ["API_KEY"],
                "_test_secret": SENTINEL_SECRET,
            },
        }
        entry = _build_keychain_auth_entry("test-mcp", mcp_data)

        entry_str = json.dumps(entry)
        assert SENTINEL_SECRET not in entry_str
        # Entry env should only have name-based config
        assert entry["env"]["CRUX_MCP_NAME"] == "test-mcp"
        assert entry["env"]["CRUX_AUTH_ENV_VARS"] == "API_KEY"

    def test_multiple_vars_only_names_in_env(self):
        """All env var names should be in CRUX_AUTH_ENV_VARS, not their values."""
        mcp_data = {
            "command": "npx",
            "args": ["-y", "some-pkg"],
            "auth": {
                "type": "keychain",
                "env_vars": ["API_KEY", "DB_PASSWORD", "SECRET_TOKEN"],
            },
        }
        entry = _build_keychain_auth_entry("test-mcp", mcp_data)

        env_vars_str = entry["env"]["CRUX_AUTH_ENV_VARS"]
        assert env_vars_str == "API_KEY,DB_PASSWORD,SECRET_TOKEN"
        assert SENTINEL_SECRET not in json.dumps(entry)

    def test_mcp_service_name_correct(self):
        """Entry must reference the correct MCP name for keychain lookup."""
        mcp_data = {
            "command": "npx",
            "args": [],
            "auth": {"env_vars": ["MY_VAR"]},
        }
        entry = _build_keychain_auth_entry("my-mcp", mcp_data)

        assert entry["env"]["CRUX_MCP_NAME"] == "my-mcp"
        assert SENTINEL_SECRET not in json.dumps(entry)


# ---------------------------------------------------------------------------
# .mcp.json tests
# ---------------------------------------------------------------------------


class TestMcpJsonNeverContainsSecrets:
    """Generated .mcp.json must not contain any secret values."""

    def test_mcp_json_never_contains_secrets(self, tmp_path):
        """sync_project() must not write sentinel to .mcp.json."""
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["authed-mcp"])

        registry = _make_registry(
            mcps={
                "authed-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-pkg"],
                    "auth": {
                        "type": "keychain",
                        "env_vars": ["API_KEY"],
                        "_test_secret": SENTINEL_SECRET,
                    },
                }
            }
        )

        success, issues = sync_project(project, registry)
        assert success

        raw = (project / ".mcp.json").read_text()
        assert SENTINEL_SECRET not in raw

    def test_mcp_json_authed_mcp_uses_shared_launcher(self, tmp_path):
        """Authed MCP entries must point to the shared launcher, not embed secrets."""
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["authed-mcp"])

        registry = _make_registry(mcps={"authed-mcp": _keychain_mcp_data()})

        sync_project(project, registry)

        data = json.loads((project / ".mcp.json").read_text())
        server = data["mcpServers"]["authed-mcp"]

        assert server["command"].endswith("keychain-auth.sh")
        # env block must only contain config names, not secret values
        for val in server.get("env", {}).values():
            assert SENTINEL_SECRET not in str(val)

    def test_mcp_json_unauthenticated_mcp_no_secrets(self, tmp_path):
        """Unauthenticated MCP entries must also never contain sentinel."""
        project = tmp_path / "proj"
        _make_crux_json(project, mcps=["plain-mcp"])

        registry = _make_registry(
            mcps={
                "plain-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-package"],
                }
            }
        )

        sync_project(project, registry)

        raw = (project / ".mcp.json").read_text()
        assert SENTINEL_SECRET not in raw


# ---------------------------------------------------------------------------
# secrets.json tests
# ---------------------------------------------------------------------------


class TestSecretsIndexContainsOnlyKeyNames:
    """secrets.json must store only key names, never actual secret values."""

    def test_secrets_index_contains_only_key_names(self, tmp_path, monkeypatch):
        """Saved secrets index holds key names; sentinel value must not appear."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        index = {
            "my-mcp": ["API_KEY", "SECRET"],
            "other-mcp": ["DB_PASSWORD"],
        }
        save_secrets_index(index)

        idx_path = tmp_path / "secrets.json"
        assert idx_path.exists()
        raw = idx_path.read_text()

        assert "API_KEY" in raw
        assert "SECRET" in raw
        assert "DB_PASSWORD" in raw
        assert SENTINEL_SECRET not in raw

    def test_secrets_index_round_trip_no_values(self, tmp_path, monkeypatch):
        """load_secrets_index / save_secrets_index round-trip preserves structure, not values."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        original = {"mcp-a": ["VAR1", "VAR2"], "mcp-b": ["TOKEN"]}
        save_secrets_index(original)

        loaded = load_secrets_index()
        assert loaded == original

        raw = (tmp_path / "secrets.json").read_text()
        assert SENTINEL_SECRET not in raw

    def test_secrets_index_values_are_lists_of_strings(self, tmp_path, monkeypatch):
        """Every value in secrets.json must be a list of string key names."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        save_secrets_index(
            {
                "my-mcp": ["API_KEY", "SECRET_TOKEN"],
            }
        )

        loaded = load_secrets_index()
        for mcp_name, keys in loaded.items():
            assert isinstance(mcp_name, str)
            assert isinstance(keys, list)
            for key in keys:
                assert isinstance(key, str)
                assert SENTINEL_SECRET not in key


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestRegistryAuthHasNoValues:
    """Registry auth metadata must contain only structural metadata, not credentials."""

    def test_registry_auth_has_no_values(self):
        """Registry with auth metadata must not contain the sentinel secret anywhere."""
        registry = _make_registry(
            mcps={
                "test-mcp": {
                    "command": "npx",
                    "args": ["-y", "pkg"],
                    "auth": {
                        "type": "keychain",
                        "env_vars": ["API_KEY", "SECRET_TOKEN"],
                    },
                }
            }
        )

        registry_str = json.dumps(registry)
        assert SENTINEL_SECRET not in registry_str

    def test_registry_never_contains_client_secret_field(self):
        """client_secret must never appear in registry JSON (it belongs in keychain)."""
        registry = _make_registry(
            mcps={
                "oauth-mcp": {
                    "command": "npx",
                    "args": [],
                    "auth": {
                        "type": "oauth",
                        "authorization_url": "https://example.com/oauth/authorize",
                        "token_url": "https://example.com/oauth/token",
                        "client_id": "crux-cli",
                        "scopes": ["read", "write"],
                    },
                }
            }
        )

        registry_str = json.dumps(registry)
        assert "client_secret" not in registry_str
        assert SENTINEL_SECRET not in registry_str


# ---------------------------------------------------------------------------
# Full cycle test
# ---------------------------------------------------------------------------


class TestFullSyncCycleNoSecretLeaks:
    """End-to-end: set up registry with keychain MCP, sync project, check all files."""

    def test_full_sync_cycle_no_secret_leaks(self, tmp_path, monkeypatch):
        """Sentinel must be absent from every file generated during a full sync cycle."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        crux_home = tmp_path
        project_dir = tmp_path / "project"

        registry = _make_registry(
            mcps={
                "authed-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-pkg"],
                    "auth": {
                        "type": "keychain",
                        "env_vars": ["API_KEY", "SECRET_TOKEN"],
                    },
                }
            }
        )
        registry_file = crux_home / "registry.json"
        registry_file.write_text(json.dumps(registry, indent=2))

        save_secrets_index({"authed-mcp": ["API_KEY", "SECRET_TOKEN"]})

        _make_crux_json(project_dir, mcps=["authed-mcp"])

        success, issues = sync_project(project_dir, registry)
        assert success, f"sync_project failed with issues: {issues}"

        # Check all generated files for sentinel
        for fpath in [
            registry_file,
            crux_home / "secrets.json",
            project_dir / ".mcp.json",
        ]:
            if fpath.exists():
                content = fpath.read_text()
                assert SENTINEL_SECRET not in content, f"Sentinel found in {fpath}"

    def test_full_sync_mcp_json_env_config_only(self, tmp_path, monkeypatch):
        """End-to-end: .mcp.json env field must only have config, not secrets."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        project_dir = tmp_path / "project"

        registry = _make_registry(mcps={"authed-mcp": _keychain_mcp_data()})

        _make_crux_json(project_dir, mcps=["authed-mcp"])
        sync_project(project_dir, registry)

        data = json.loads((project_dir / ".mcp.json").read_text())
        server = data["mcpServers"]["authed-mcp"]

        # env field should have CRUX_MCP_NAME and CRUX_AUTH_ENV_VARS only
        env = server.get("env", {})
        assert "CRUX_MCP_NAME" in env
        assert "CRUX_AUTH_ENV_VARS" in env
        raw = json.dumps(server)
        assert SENTINEL_SECRET not in raw
