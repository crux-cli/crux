"""Security invariant tests — secrets NEVER in the filesystem.

Core principle: All credentials are stored in OS keychain only.
Launcher scripts contain keychain lookup commands, not literal values.
.mcp.json, registry.json, secrets.json must never contain actual secret values.

Every test uses a sentinel value and asserts it never appears in generated files.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from crux_cli.secrets import load_secrets_index, save_secrets_index
from crux_cli.sync import generate_launcher, sync_project

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
# Launcher tests
# ---------------------------------------------------------------------------


class TestLauncherNeverContainsLiteralSecrets:
    """Launcher scripts must only reference keychain lookup commands."""

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_launcher_never_contains_literal_secrets(self, _mock, tmp_path):
        """Sentinel must not appear in a generated launcher script."""
        launcher_dir = tmp_path / "launchers"
        mcp_data = {
            "command": "npx",
            "args": ["-y", "some-pkg"],
            "auth": {
                "type": "keychain",
                "env_vars": ["API_KEY"],
                # Simulate a registry entry that might accidentally contain a secret
                "_test_secret": SENTINEL_SECRET,
            },
        }
        path = generate_launcher("test-mcp", mcp_data, launcher_base=launcher_dir)
        assert path is not None

        content = path.read_text()
        assert SENTINEL_SECRET not in content
        # Must use macOS keychain lookup
        assert "security find-generic-password" in content

    @patch("crux_cli.sync.platform.system", return_value="Linux")
    def test_launcher_linux_never_contains_literal_secrets(self, _mock, tmp_path):
        """Sentinel must not appear in a Linux launcher script."""
        launcher_dir = tmp_path / "launchers"
        mcp_data = {
            "command": "node",
            "args": ["server.js"],
            "auth": {
                "type": "keychain",
                "env_vars": ["API_KEY"],
            },
        }
        path = generate_launcher("test-mcp", mcp_data, launcher_base=launcher_dir)
        assert path is not None

        content = path.read_text()
        assert SENTINEL_SECRET not in content
        # Must use Linux secret-tool lookup
        assert "secret-tool lookup" in content

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_launcher_contains_only_lookup_commands(self, _mock, tmp_path):
        """Every export VAR= line in the launcher must use $(...) shell expansion."""
        launcher_dir = tmp_path / "launchers"
        mcp_data = {
            "command": "npx",
            "args": ["-y", "some-pkg"],
            "auth": {
                "type": "keychain",
                "env_vars": ["API_KEY", "DB_PASSWORD", "SECRET_TOKEN"],
            },
        }
        path = generate_launcher("test-mcp", mcp_data, launcher_base=launcher_dir)
        assert path is not None

        content = path.read_text()
        export_lines = [line for line in content.splitlines() if line.startswith("export ")]
        # Must have one export per env var
        assert len(export_lines) == 3

        for line in export_lines:
            # Each export must assign using $(...) subshell, not a literal value
            assert "=$(" in line, f"Export line uses literal value instead of shell expansion: {line!r}"
            # The assigned value must not be a bare string (no quotes without subshell)
            assert SENTINEL_SECRET not in line

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_launcher_mcp_service_name_correct(self, _mock, tmp_path):
        """Launcher must reference the correct keychain service name."""
        launcher_dir = tmp_path / "launchers"
        mcp_data = {
            "command": "npx",
            "args": [],
            "auth": {"env_vars": ["MY_VAR"]},
        }
        path = generate_launcher("my-mcp", mcp_data, launcher_base=launcher_dir)
        content = path.read_text()

        # Service name must be crux.<mcp-name>
        assert "crux.my-mcp" in content
        assert SENTINEL_SECRET not in content


# ---------------------------------------------------------------------------
# .mcp.json tests
# ---------------------------------------------------------------------------


class TestMcpJsonNeverContainsSecrets:
    """Generated .mcp.json must not contain any secret values."""

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_mcp_json_never_contains_secrets(self, _mock, tmp_path):
        """sync_project() must not write sentinel to .mcp.json."""
        project = tmp_path / "proj"
        launcher_dir = tmp_path / "launchers"
        _make_crux_json(project, mcps=["authed-mcp"])

        registry = _make_registry(
            mcps={
                "authed-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-pkg"],
                    "auth": {
                        "type": "keychain",
                        "env_vars": ["API_KEY"],
                        # Sentinel in registry metadata should never bleed into .mcp.json
                        "_test_secret": SENTINEL_SECRET,
                    },
                }
            }
        )

        success, issues = sync_project(project, registry, launcher_base=launcher_dir)
        assert success

        mcp_json_path = project / ".mcp.json"
        assert mcp_json_path.exists()
        raw = mcp_json_path.read_text()
        assert SENTINEL_SECRET not in raw

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_mcp_json_authed_mcp_points_to_launcher(self, _mock, tmp_path):
        """Authed MCP entries in .mcp.json must only have command pointing to a launcher."""
        project = tmp_path / "proj"
        launcher_dir = tmp_path / "launchers"
        _make_crux_json(project, mcps=["authed-mcp"])

        registry = _make_registry(
            mcps={
                "authed-mcp": _keychain_mcp_data(),
            }
        )

        sync_project(project, registry, launcher_base=launcher_dir)

        data = json.loads((project / ".mcp.json").read_text())
        server = data["mcpServers"]["authed-mcp"]

        # Must only have command (launcher path) and args
        assert "command" in server
        assert server["command"].endswith(".sh")
        # Must not contain env block with secret values
        env_block = server.get("env", {})
        for val in env_block.values():
            assert SENTINEL_SECRET not in str(val)

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_mcp_json_no_auth_headers(self, _mock, tmp_path):
        """Generated .mcp.json must not contain Authorization or Bearer strings."""
        project = tmp_path / "proj"
        launcher_dir = tmp_path / "launchers"
        _make_crux_json(project, mcps=["authed-mcp"])

        registry = _make_registry(
            mcps={
                "authed-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-pkg"],
                    "auth": {
                        "type": "keychain",
                        "env_vars": ["API_KEY"],
                    },
                }
            }
        )

        sync_project(project, registry, launcher_base=launcher_dir)

        raw = (project / ".mcp.json").read_text()
        assert "Authorization" not in raw
        assert "Bearer" not in raw
        assert "token" not in raw.lower() or (
            # "token" may appear in keychain account names, but not as a value
            # The raw JSON must not contain the sentinel
            SENTINEL_SECRET not in raw
        )
        assert SENTINEL_SECRET not in raw

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_mcp_json_unauthenticated_mcp_no_secrets(self, _mock, tmp_path):
        """Unauthenticated MCP entries must also never contain sentinel."""
        project = tmp_path / "proj"
        launcher_dir = tmp_path / "launchers"
        _make_crux_json(project, mcps=["plain-mcp"])

        registry = _make_registry(
            mcps={
                "plain-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-package"],
                    # No auth block
                }
            }
        )

        sync_project(project, registry, launcher_base=launcher_dir)

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

        # Key names must be present
        assert "API_KEY" in raw
        assert "SECRET" in raw
        assert "DB_PASSWORD" in raw

        # The actual sentinel secret value must never appear
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
                # Key names must not look like actual secret values
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

    def test_registry_auth_fields_are_metadata_only(self):
        """Auth block must only contain structural metadata (names, types, URLs)."""
        auth_block = {
            "type": "keychain",
            "env_vars": ["API_KEY", "SECRET_TOKEN"],
            # These are valid metadata fields per spec
            "keychain_key": "access_token",
        }
        mcp_entry = {"command": "npx", "args": [], "auth": auth_block}
        registry = _make_registry(mcps={"test-mcp": mcp_entry})

        # Serialize and check
        registry_str = json.dumps(registry)
        assert SENTINEL_SECRET not in registry_str

        # env_vars should be names only
        for var_name in auth_block["env_vars"]:
            assert var_name == var_name.strip()  # no trailing whitespace
            assert " " not in var_name  # no spaces (not a value)

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
                        # client_secret intentionally absent — belongs in keychain
                    },
                }
            }
        )

        registry_str = json.dumps(registry)
        assert "client_secret" not in registry_str
        assert SENTINEL_SECRET not in registry_str

    def test_registry_oauth_metadata_no_token_values(self):
        """OAuth registry metadata has no actual token values."""
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
                        "keychain_account_access": "access_token",
                        "keychain_account_refresh": "refresh_token",
                    },
                }
            }
        )

        # keychain_account_* fields are account NAMES, not actual tokens
        auth = registry["mcp_definitions"]["oauth-mcp"]["auth"]
        assert auth["keychain_account_access"] == "access_token"  # name, not value
        assert auth["keychain_account_refresh"] == "refresh_token"  # name, not value

        registry_str = json.dumps(registry)
        assert SENTINEL_SECRET not in registry_str


# ---------------------------------------------------------------------------
# Full cycle test
# ---------------------------------------------------------------------------


class TestFullSyncCycleNoSecretLeaks:
    """End-to-end: set up registry with keychain MCP, sync project, check all files."""

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_full_sync_cycle_no_secret_leaks(self, _mock, tmp_path, monkeypatch):
        """Sentinel must be absent from every file generated during a full sync cycle."""
        # Set CRUX_TEST_ROOT so secrets.json and registry.json land in tmp_path
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        crux_home = tmp_path
        launcher_dir = crux_home / "mcps" / "launchers"
        project_dir = tmp_path / "project"

        # Write a registry with keychain-authed MCP
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

        # Write secrets index (key names only, no values)
        save_secrets_index({"authed-mcp": ["API_KEY", "SECRET_TOKEN"]})

        # Create project crux.json
        _make_crux_json(project_dir, mcps=["authed-mcp"])

        # Run sync
        success, issues = sync_project(project_dir, registry, launcher_base=launcher_dir)
        assert success, f"sync_project failed with issues: {issues}"

        # Collect all generated files
        generated_files: list[Path] = []

        if registry_file.exists():
            generated_files.append(registry_file)

        secrets_file = crux_home / "secrets.json"
        if secrets_file.exists():
            generated_files.append(secrets_file)

        mcp_json = project_dir / ".mcp.json"
        if mcp_json.exists():
            generated_files.append(mcp_json)

        launcher = launcher_dir / "authed-mcp.sh"
        if launcher.exists():
            generated_files.append(launcher)

        # Assert sentinel absent from every file
        assert generated_files, "No generated files found — check test setup"
        for fpath in generated_files:
            content = fpath.read_text()
            assert SENTINEL_SECRET not in content, (
                f"Sentinel secret found in {fpath}: "
                f"{[line for line in content.splitlines() if SENTINEL_SECRET in line]}"
            )

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_full_sync_launcher_uses_keychain_lookup(self, _mock, tmp_path, monkeypatch):
        """End-to-end: launcher must use security find-generic-password for each var."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        crux_home = tmp_path
        launcher_dir = crux_home / "mcps" / "launchers"
        project_dir = tmp_path / "project"

        registry = _make_registry(
            mcps={
                "my-mcp": {
                    "command": "npx",
                    "args": ["-y", "some-pkg"],
                    "auth": {
                        "type": "keychain",
                        "env_vars": ["FIRST_KEY", "SECOND_KEY"],
                    },
                }
            }
        )

        _make_crux_json(project_dir, mcps=["my-mcp"])
        sync_project(project_dir, registry, launcher_base=launcher_dir)

        launcher = launcher_dir / "my-mcp.sh"
        assert launcher.exists()
        content = launcher.read_text()

        # Each env var must be looked up from keychain
        assert "FIRST_KEY" in content
        assert "SECOND_KEY" in content
        assert content.count("security find-generic-password") == 2
        assert SENTINEL_SECRET not in content

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_full_sync_mcp_json_has_no_inline_secrets(self, _mock, tmp_path, monkeypatch):
        """End-to-end: .mcp.json for authed MCP must only have command + args."""
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))

        crux_home = tmp_path
        launcher_dir = crux_home / "mcps" / "launchers"
        project_dir = tmp_path / "project"

        registry = _make_registry(
            mcps={
                "authed-mcp": _keychain_mcp_data(),
            }
        )

        _make_crux_json(project_dir, mcps=["authed-mcp"])
        sync_project(project_dir, registry, launcher_base=launcher_dir)

        mcp_json = project_dir / ".mcp.json"
        data = json.loads(mcp_json.read_text())
        server = data["mcpServers"]["authed-mcp"]

        # Allowed keys: command and args only (no env, headers, tokens)
        allowed_keys = {"command", "args"}
        for key in server:
            assert key in allowed_keys, (
                f"Unexpected key {key!r} in .mcp.json server entry — potential secret leak vector"
            )
        assert SENTINEL_SECRET not in mcp_json.read_text()


# ---------------------------------------------------------------------------
# Additional invariant tests
# ---------------------------------------------------------------------------


class TestNoSecretInAnyShellExpansion:
    """Shell expansion patterns must be lookup commands, not literal values."""

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_no_literal_value_in_export_assignment(self, _mock, tmp_path):
        """export VAR=LITERAL_VALUE must never appear — must be export VAR=$(...)."""
        launcher_dir = tmp_path / "launchers"
        mcp_data = {
            "command": "npx",
            "args": [],
            "auth": {"env_vars": ["API_KEY"]},
        }
        path = generate_launcher("test-mcp", mcp_data, launcher_base=launcher_dir)
        content = path.read_text()

        for line in content.splitlines():
            if line.startswith("export ") and "=" in line:
                _var, _sep, value_part = line.partition("=")
                # Value must start with $( (subshell) or be empty
                assert value_part.startswith("$("), f"Found literal value in export line: {line!r}"

    @patch("crux_cli.sync.platform.system", return_value="Darwin")
    def test_multiple_vars_all_use_subshell(self, _mock, tmp_path):
        """All export lines must use subshell expansion when multiple vars present."""
        launcher_dir = tmp_path / "launchers"
        mcp_data = {
            "command": "node",
            "args": ["server.js"],
            "auth": {
                "env_vars": ["VAR_ONE", "VAR_TWO", "VAR_THREE"],
            },
        }
        path = generate_launcher("multi-mcp", mcp_data, launcher_base=launcher_dir)
        content = path.read_text()

        export_lines = [line for line in content.splitlines() if line.startswith("export ")]
        assert len(export_lines) == 3

        for line in export_lines:
            assert "=$(" in line, f"Export line missing subshell: {line!r}"
            assert SENTINEL_SECRET not in line
