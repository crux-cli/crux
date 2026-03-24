"""Unit tests for crux_cli.auth — unified auth orchestration module."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry(mcp_name: str, auth: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal registry dict with a single MCP."""
    return {"mcp_definitions": {mcp_name: {"auth": auth}}}


class MockBackend:
    """Simple in-memory secrets backend for testing."""

    def __init__(self, data: dict[str, str] | None = None):
        self._data: dict[tuple[str, str], str] = {}
        if data:
            for (mcp, key), val in data.items():
                self._data[(mcp, key)] = val
        self.set_calls: list[tuple[str, str, str]] = []

    def get(self, mcp_name: str, key: str) -> str | None:
        return self._data.get((mcp_name, key))

    def set(self, mcp_name: str, key: str, value: str) -> None:  # noqa: A003
        self._data[(mcp_name, key)] = value
        self.set_calls.append((mcp_name, key, value))

    def delete(self, mcp_name: str, key: str) -> None:
        self._data.pop((mcp_name, key), None)

    def list_keys(self, mcp_name: str | None = None) -> dict[str, list[str]]:
        return {}


# ---------------------------------------------------------------------------
# auth_status tests
# ---------------------------------------------------------------------------


class TestAuthStatus:
    def test_auth_status_keychain_missing(self, monkeypatch):
        """Keychain MCP with missing secrets → status 'Missing: VAR'."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        from crux_cli.auth import auth_status

        registry = _make_registry("mymcp", {"type": "keychain", "env_vars": ["API_KEY"]})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["name"] == "mymcp"
        assert results[0]["auth_type"] == "keychain"
        assert results[0]["status"] == "Missing: API_KEY"

    def test_auth_status_keychain_present(self, monkeypatch):
        """Keychain MCP with all secrets stored → status 'Authenticated'."""
        monkeypatch.setattr(
            "crux_cli.auth.load_secrets_index",
            lambda: {"mymcp": ["API_KEY", "SECRET"]},
        )

        from crux_cli.auth import auth_status

        registry = _make_registry("mymcp", {"type": "keychain", "env_vars": ["API_KEY", "SECRET"]})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["status"] == "Authenticated"

    def test_auth_status_external_cli_ok(self, monkeypatch):
        """external-cli MCP where check_cmd returns 0 → 'Authenticated'."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        def mock_run(cmd, **kwargs):
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr("crux_cli.auth.subprocess.run", mock_run)

        from crux_cli.auth import auth_status

        registry = _make_registry("ghcli", {"type": "external-cli", "check_cmd": ["gh", "auth", "status"]})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["status"] == "Authenticated"

    def test_auth_status_external_cli_fail(self, monkeypatch):
        """external-cli MCP where check_cmd returns non-zero → 'Not authenticated'."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        def mock_run(cmd, **kwargs):
            return SimpleNamespace(returncode=1)

        monkeypatch.setattr("crux_cli.auth.subprocess.run", mock_run)

        from crux_cli.auth import auth_status

        registry = _make_registry("ghcli", {"type": "external-cli", "check_cmd": ["gh", "auth", "status"]})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["status"] == "Not authenticated"

    def test_auth_status_bearer_set(self, monkeypatch):
        """Bearer MCP where backend.get returns a value → 'Authenticated'."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        mock_backend = MockBackend()
        mock_backend._data[("mymcp", "API_TOKEN")] = "secret-value"
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import auth_status

        registry = _make_registry("mymcp", {"type": "bearer", "keychain_key": "API_TOKEN"})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["status"] == "Authenticated"

    def test_auth_status_bearer_missing(self, monkeypatch):
        """Bearer MCP where backend.get returns None → 'Token not set'."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import auth_status

        registry = _make_registry("mymcp", {"type": "bearer", "keychain_key": "API_TOKEN"})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["status"] == "Token not set"

    def test_auth_status_setup_cmd(self, monkeypatch):
        """setup-cmd MCP always returns 'Run setup to configure'."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        from crux_cli.auth import auth_status

        registry = _make_registry("mymcp", {"type": "setup-cmd", "setup_cmd": ["some-tool", "setup"]})
        results = auth_status(registry)

        assert len(results) == 1
        assert results[0]["status"] == "Run setup to configure"

    def test_auth_status_no_auth_mcps_excluded(self, monkeypatch):
        """MCPs without auth block are excluded from auth_status results."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})

        from crux_cli.auth import auth_status

        registry = {
            "mcp_definitions": {
                "no-auth-mcp": {"command": ["some-tool"]},
                "auth-mcp": {"auth": {"type": "keychain", "env_vars": ["KEY"]}},
            }
        }
        results = auth_status(registry)

        names = [r["name"] for r in results]
        assert "no-auth-mcp" not in names
        assert "auth-mcp" in names


# ---------------------------------------------------------------------------
# auth_single tests
# ---------------------------------------------------------------------------


class TestAuthSingle:
    def test_auth_single_unknown_type_raises(self, monkeypatch):
        """auth_single with unknown auth type raises ValueError."""
        from crux_cli.auth import auth_single

        registry = _make_registry("mymcp", {"type": "bogus"})

        import pytest

        with pytest.raises(ValueError, match="Unknown auth type 'bogus'"):
            auth_single("mymcp", registry)

    def test_auth_single_keychain_prompts(self, monkeypatch):
        """auth_single keychain prompts for each var and calls backend.set."""
        monkeypatch.setattr(
            "crux_cli.auth.load_secrets_index",
            lambda: {},
        )

        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)
        monkeypatch.setattr("crux_cli.auth.getpass.getpass", lambda prompt: "test-secret")

        from crux_cli.auth import auth_single

        registry = _make_registry("mymcp", {"type": "keychain", "env_vars": ["API_KEY", "API_SECRET"]})
        auth_single("mymcp", registry)

        # backend.set should be called once per env var
        assert len(mock_backend.set_calls) == 2
        keys_stored = [call[1] for call in mock_backend.set_calls]
        assert "API_KEY" in keys_stored
        assert "API_SECRET" in keys_stored
        # values should be what getpass returned
        for call in mock_backend.set_calls:
            assert call[2] == "test-secret"

    def test_auth_keychain_skips_already_stored(self, monkeypatch, capsys):
        """_auth_keychain skips vars already in the secrets index and backend."""
        monkeypatch.setattr(
            "crux_cli.auth.load_secrets_index",
            lambda: {"mymcp": ["API_KEY"]},
        )

        mock_backend = MockBackend()
        mock_backend._data[("mymcp", "API_KEY")] = "existing"
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)
        monkeypatch.setattr("crux_cli.auth.getpass.getpass", lambda prompt: "new-secret")

        from crux_cli.auth import _auth_keychain

        _auth_keychain("mymcp", {"type": "keychain", "env_vars": ["API_KEY", "NEW_VAR"]})

        # Only NEW_VAR should be prompted and stored; API_KEY should be skipped
        assert len(mock_backend.set_calls) == 1
        assert mock_backend.set_calls[0][1] == "NEW_VAR"

    def test_auth_single_mcp_not_found(self, monkeypatch, capsys):
        """auth_single with nonexistent MCP name calls sys.exit(1)."""
        import pytest

        from crux_cli.auth import auth_single

        registry = {"mcp_definitions": {}}

        with pytest.raises(SystemExit) as exc_info:
            auth_single("nonexistent", registry)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "nonexistent" in captured.out


# ---------------------------------------------------------------------------
# --value inline auth tests
# ---------------------------------------------------------------------------


class TestInlineValueAuth:
    """Test that --value flag sets secrets non-interactively."""

    def test_keychain_inline_values_stored(self, monkeypatch):
        """Inline values are stored without prompting."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})
        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import auth_single

        registry = _make_registry("mymcp", {"type": "keychain", "env_vars": ["API_KEY", "SECRET"]})
        auth_single("mymcp", registry, inline_values={"API_KEY": "key123", "SECRET": "sec456"})

        assert len(mock_backend.set_calls) == 2
        stored = {call[1]: call[2] for call in mock_backend.set_calls}
        assert stored["API_KEY"] == "key123"
        assert stored["SECRET"] == "sec456"  # noqa: S105

    def test_keychain_inline_overwrites_existing(self, monkeypatch):
        """Inline values overwrite already-stored secrets."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {"mymcp": ["API_KEY"]})
        mock_backend = MockBackend()
        mock_backend._data[("mymcp", "API_KEY")] = "old-value"
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import _auth_keychain

        _auth_keychain("mymcp", {"env_vars": ["API_KEY"]}, inline_values={"API_KEY": "new-value"})

        assert len(mock_backend.set_calls) == 1
        assert mock_backend.set_calls[0][2] == "new-value"

    def test_keychain_inline_partial_skips_missing(self, monkeypatch, capsys):
        """When inline_values provided but a var is missing, it's skipped without prompting."""
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})
        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import _auth_keychain

        _auth_keychain("mymcp", {"env_vars": ["API_KEY", "SECRET"]}, inline_values={"API_KEY": "key123"})

        assert len(mock_backend.set_calls) == 1
        assert mock_backend.set_calls[0][1] == "API_KEY"
        captured = capsys.readouterr()
        assert "Skipped SECRET" in captured.out

    def test_bearer_inline_value_stored(self, monkeypatch):
        """Inline value for bearer token is stored without prompting."""
        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import _auth_bearer

        _auth_bearer("mymcp", {"keychain_key": "API_TOKEN"}, inline_values={"API_TOKEN": "mytoken"})

        assert len(mock_backend.set_calls) == 1
        assert mock_backend.set_calls[0][2] == "mytoken"

    def test_bearer_inline_overwrites_existing(self, monkeypatch):
        """Inline bearer token overwrites existing without prompting."""
        mock_backend = MockBackend()
        mock_backend._data[("mymcp", "API_TOKEN")] = "old-token"
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.auth import _auth_bearer

        _auth_bearer("mymcp", {"keychain_key": "API_TOKEN"}, inline_values={"API_TOKEN": "new-token"})

        assert len(mock_backend.set_calls) == 1
        assert mock_backend.set_calls[0][2] == "new-token"


# ---------------------------------------------------------------------------
# Inline auth during mcp add
# ---------------------------------------------------------------------------


class TestInlineAuthDuringAdd:
    """Test that cmd_mcp_add prompts for keychain secrets inline."""

    def test_add_with_keychain_prompts_inline(self, monkeypatch, tmp_path):
        """When --keychain is provided and stdin is a TTY, secrets are prompted inline."""
        crux_dir = tmp_path / ".crux"
        crux_dir.mkdir()
        (crux_dir / "registry.json").write_text(
            json.dumps({"version": "1.0.0", "mcp_definitions": {}, "skill_definitions": {}})
        )
        monkeypatch.setenv("CRUX_TEST_ROOT", str(crux_dir))
        monkeypatch.delenv("CRUX_HOME", raising=False)

        # Mock stdin as TTY
        monkeypatch.setattr("sys.stdin", SimpleNamespace(isatty=lambda: True))

        # Mock auth backend
        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)
        monkeypatch.setattr("crux_cli.auth.load_secrets_index", lambda: {})
        monkeypatch.setattr("crux_cli.auth.getpass.getpass", lambda prompt: "test-secret")

        from crux_cli.cli.commands.mcp import cmd_mcp_add

        args = argparse.Namespace(
            name="test-mcp",
            npx="@test/pkg",
            uvx=None,
            github=None,
            local=None,
            command=None,
            args=None,
            tags=None,
            keychain="API_KEY,SECRET",
            build_cmd=None,
        )
        cmd_mcp_add(args)

        # Backend should have received set() calls for each keychain var
        assert len(mock_backend.set_calls) == 2
        keys_stored = [call[1] for call in mock_backend.set_calls]
        assert "API_KEY" in keys_stored
        assert "SECRET" in keys_stored

    def test_add_with_keychain_skips_when_not_tty(self, monkeypatch, tmp_path):
        """When stdin is not a TTY, inline auth is skipped."""
        crux_dir = tmp_path / ".crux"
        crux_dir.mkdir()
        (crux_dir / "registry.json").write_text(
            json.dumps({"version": "1.0.0", "mcp_definitions": {}, "skill_definitions": {}})
        )
        monkeypatch.setenv("CRUX_TEST_ROOT", str(crux_dir))
        monkeypatch.delenv("CRUX_HOME", raising=False)

        # Mock stdin as NOT a TTY
        monkeypatch.setattr("sys.stdin", SimpleNamespace(isatty=lambda: False))

        mock_backend = MockBackend()
        monkeypatch.setattr("crux_cli.auth.get_backend", lambda: mock_backend)

        from crux_cli.cli.commands.mcp import cmd_mcp_add

        args = argparse.Namespace(
            name="test-mcp2",
            npx="@test/pkg",
            uvx=None,
            github=None,
            local=None,
            command=None,
            args=None,
            tags=None,
            keychain="API_KEY",
            build_cmd=None,
        )
        cmd_mcp_add(args)

        # Backend should NOT have received any set() calls
        assert len(mock_backend.set_calls) == 0
