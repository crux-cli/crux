"""Unit tests for crux_cli.oauth — PKCE, token metadata, discovery."""

import base64
import hashlib

from crux_cli.oauth import (
    generate_pkce,
    load_token_metadata,
    save_token_metadata,
)


class TestPKCE:
    def test_verifier_length(self):
        verifier, _ = generate_pkce()
        assert len(verifier) >= 32

    def test_challenge_is_s256(self):
        verifier, challenge = generate_pkce()
        expected = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        )
        assert challenge == expected

    def test_unique_each_call(self):
        v1, _ = generate_pkce()
        v2, _ = generate_pkce()
        assert v1 != v2


class TestTokenMetadata:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("crux_cli.oauth.tokens_path", lambda: tmp_path / "tokens.json")
        meta = {"test-mcp": {"auth_type": "oauth", "expires_at": "2026-01-01T00:00:00+00:00"}}
        save_token_metadata(meta)
        loaded = load_token_metadata()
        assert loaded == meta

    def test_load_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("crux_cli.oauth.tokens_path", lambda: tmp_path / "nope.json")
        assert load_token_metadata() == {}

    def test_load_corrupt_file(self, tmp_path, monkeypatch):
        bad = tmp_path / "tokens.json"
        bad.write_text("NOT JSON")
        monkeypatch.setattr("crux_cli.oauth.tokens_path", lambda: bad)
        assert load_token_metadata() == {}

    def test_file_permissions(self, tmp_path, monkeypatch):
        monkeypatch.setattr("crux_cli.oauth.tokens_path", lambda: tmp_path / "tokens.json")
        save_token_metadata({"x": {}})
        perms = (tmp_path / "tokens.json").stat().st_mode & 0o777
        assert perms == 0o600

    def test_tokens_json_never_contains_token_values(self, tmp_path, monkeypatch):
        """Security: tokens.json stores metadata only, never actual tokens."""
        monkeypatch.setattr("crux_cli.oauth.tokens_path", lambda: tmp_path / "tokens.json")
        meta = {
            "my-mcp": {
                "auth_type": "oauth",
                "keychain_account_access": "access_token",
                "keychain_account_refresh": "refresh_token",
                "expires_at": "2026-01-01T00:00:00+00:00",
                "scopes": ["read"],
                "token_url": "https://example.com/token",
                "client_id": "crux",
            }
        }
        save_token_metadata(meta)
        content = (tmp_path / "tokens.json").read_text()
        # Should contain only metadata keys, never anything that looks like a token
        assert "sk-" not in content
        assert "eyJ" not in content  # JWT prefix
        # Should contain the metadata
        assert "keychain_account_access" in content
        assert "expires_at" in content
