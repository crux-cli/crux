"""Unit tests for crux_cli.bridge — stdio-to-HTTP proxy."""

import json

from crux_cli.bridge import _build_auth_header, _make_error_response


class TestBuildAuthHeader:
    def test_full_header(self, monkeypatch):
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_HEADER", "Authorization")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_PREFIX", "Bearer")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_ENV", "MY_TOKEN")
        monkeypatch.setenv("MY_TOKEN", "secret123")
        result = _build_auth_header()
        assert result == {"Authorization": "Bearer secret123"}

    def test_no_prefix(self, monkeypatch):
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_HEADER", "X-API-Key")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_PREFIX", "")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_ENV", "MY_KEY")
        monkeypatch.setenv("MY_KEY", "abc123")
        result = _build_auth_header()
        assert result == {"X-API-Key": "abc123"}

    def test_missing_token_env(self, monkeypatch):
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_HEADER", "Authorization")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_PREFIX", "Bearer")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_ENV", "MISSING_VAR")
        monkeypatch.delenv("MISSING_VAR", raising=False)
        result = _build_auth_header()
        assert result == {}

    def test_missing_header_name(self, monkeypatch):
        monkeypatch.delenv("CRUX_BRIDGE_AUTH_HEADER", raising=False)
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_ENV", "MY_TOKEN")
        monkeypatch.setenv("MY_TOKEN", "secret")
        result = _build_auth_header()
        assert result == {}

    def test_token_never_in_sys_argv(self, monkeypatch):
        """Security: token comes from env, never from CLI args."""
        import sys

        monkeypatch.setenv("CRUX_BRIDGE_AUTH_HEADER", "Authorization")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_PREFIX", "Bearer")
        monkeypatch.setenv("CRUX_BRIDGE_AUTH_ENV", "MY_TOKEN")
        monkeypatch.setenv("MY_TOKEN", "secret-value")
        result = _build_auth_header()
        assert result["Authorization"] == "Bearer secret-value"
        # Verify token is NOT in command line arguments
        for arg in sys.argv:
            assert "secret-value" not in arg


class TestMakeErrorResponse:
    def test_error_response_format(self):
        resp = _make_error_response(1, -32000, "HTTP 401: Unauthorized")
        parsed = json.loads(resp)
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["id"] == 1
        assert parsed["error"]["code"] == -32000
        assert "401" in parsed["error"]["message"]

    def test_null_id(self):
        resp = _make_error_response(None, -32001, "Connection error")
        parsed = json.loads(resp)
        assert parsed["id"] is None
