"""Tests for secret cleanup during crux mcp remove."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from crux_cli.cli.commands.mcp import _cleanup_secrets


@pytest.fixture
def mcp_data_with_secrets():
    return {
        "auth": {
            "type": "keychain",
            "env_vars": ["API_KEY", "SECRET_TOKEN"],
        }
    }


@pytest.fixture
def mcp_data_no_auth():
    return {}


class TestCleanupSecrets:
    def test_no_auth_block_does_nothing(self, mcp_data_no_auth):
        args = argparse.Namespace(keep_secrets=False, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_no_auth, args)

    def test_no_env_vars_does_nothing(self):
        data = {"auth": {"type": "external-cli"}}
        args = argparse.Namespace(keep_secrets=False, remove_secrets=False)
        _cleanup_secrets("test-mcp", data, args)

    @patch("crux_cli.secrets.get_backend")
    def test_no_stored_secrets_does_nothing(self, mock_get_backend, mcp_data_with_secrets):
        backend = MagicMock()
        backend.get.return_value = None
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=False, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        backend.delete.assert_not_called()

    @patch("crux_cli.secrets.save_secrets_index")
    @patch("crux_cli.secrets.load_secrets_index", return_value={})
    @patch("crux_cli.secrets.get_backend")
    def test_remove_secrets_flag_deletes_all(self, mock_get_backend, _mock_idx, _mock_save, mcp_data_with_secrets):
        backend = MagicMock()
        backend.get.return_value = "stored-value"
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=False, remove_secrets=True)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        assert backend.delete.call_count == 2
        backend.delete.assert_any_call("test-mcp", "API_KEY")
        backend.delete.assert_any_call("test-mcp", "SECRET_TOKEN")

    @patch("crux_cli.secrets.get_backend")
    def test_keep_secrets_flag_skips_deletion(self, mock_get_backend, mcp_data_with_secrets, capsys):
        backend = MagicMock()
        backend.get.return_value = "stored-value"
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=True, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        backend.delete.assert_not_called()
        assert "Kept secrets" in capsys.readouterr().out

    @patch("crux_cli.secrets.save_secrets_index")
    @patch("crux_cli.secrets.load_secrets_index", return_value={"test-mcp": ["API_KEY", "SECRET_TOKEN"]})
    @patch("crux_cli.secrets.get_backend")
    @patch("builtins.input", return_value="")
    @patch("sys.stdin")
    def test_interactive_yes_default(
        self,
        mock_stdin,
        _mock_input,
        mock_get_backend,
        _mock_idx,
        _mock_save,
        mcp_data_with_secrets,
        capsys,
    ):
        mock_stdin.isatty.return_value = True
        backend = MagicMock()
        backend.get.return_value = "stored-value"
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=False, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        assert backend.delete.call_count == 2
        assert "Removed 2 secret(s)" in capsys.readouterr().out

    @patch("crux_cli.secrets.get_backend")
    @patch("builtins.input", return_value="n")
    @patch("sys.stdin")
    def test_interactive_no(self, mock_stdin, _mock_input, mock_get_backend, mcp_data_with_secrets, capsys):
        mock_stdin.isatty.return_value = True
        backend = MagicMock()
        backend.get.return_value = "stored-value"
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=False, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        backend.delete.assert_not_called()
        assert "Kept secrets" in capsys.readouterr().out

    @patch("crux_cli.secrets.get_backend")
    @patch("sys.stdin")
    def test_non_interactive_keeps_secrets(self, mock_stdin, mock_get_backend, mcp_data_with_secrets, capsys):
        mock_stdin.isatty.return_value = False
        backend = MagicMock()
        backend.get.return_value = "stored-value"
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=False, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        backend.delete.assert_not_called()
        assert "kept" in capsys.readouterr().out

    @patch("crux_cli.secrets.get_backend")
    def test_partially_stored_only_counts_stored(self, mock_get_backend, mcp_data_with_secrets, capsys):
        """Only secrets that are actually stored are counted."""
        backend = MagicMock()
        backend.get.side_effect = lambda name, key: "val" if key == "API_KEY" else None
        mock_get_backend.return_value = backend
        args = argparse.Namespace(keep_secrets=True, remove_secrets=False)
        _cleanup_secrets("test-mcp", mcp_data_with_secrets, args)
        assert "Kept secrets" in capsys.readouterr().out
