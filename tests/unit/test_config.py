"""Tests for crux_cli.config — TOML configuration management."""

from unittest.mock import patch

from crux_cli.config import (
    default_config,
    detect_secrets_backend,
    load_config,
    save_config,
)


class TestDetectSecretsBackend:
    """Platform-specific secrets backend detection."""

    def test_macos_returns_keychain(self):
        with patch("crux_cli.config.platform.system", return_value="Darwin"):
            assert detect_secrets_backend() == "keychain"

    def test_linux_returns_secret_service(self):
        with patch("crux_cli.config.platform.system", return_value="Linux"):
            assert detect_secrets_backend() == "secret-service"

    def test_windows_returns_plaintext(self):
        with patch("crux_cli.config.platform.system", return_value="Windows"):
            assert detect_secrets_backend() == "plaintext"

    def test_unknown_returns_plaintext(self):
        with patch("crux_cli.config.platform.system", return_value="FreeBSD"):
            assert detect_secrets_backend() == "plaintext"


class TestLoadConfigDefault:
    """load_config() with no file on disk returns defaults."""

    def test_load_config_default(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        cfg = load_config()
        assert "secrets" in cfg
        assert "backend" in cfg["secrets"]
        assert "paths" in cfg
        assert cfg["paths"]["crux_home"] == str(tmp_path)


class TestLoadConfigCustom:
    """load_config() reads values from a TOML file."""

    def test_load_config_custom(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('[secrets]\nbackend = "plaintext"\n\n[paths]\ncrux_home = "/custom"\n')
        cfg = load_config(path=config_file)
        assert cfg["secrets"]["backend"] == "plaintext"
        assert cfg["paths"]["crux_home"] == "/custom"

    def test_file_values_override_defaults(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        config_file = tmp_path / "config.toml"
        config_file.write_text('[secrets]\nbackend = "plaintext"\n')
        cfg = load_config(path=config_file)
        assert cfg["secrets"]["backend"] == "plaintext"
        # paths section should still have defaults
        assert "paths" in cfg


class TestSaveConfigRoundtrip:
    """save_config() followed by load_config() preserves values."""

    def test_save_config_roundtrip(self, tmp_path):
        config_file = tmp_path / "subdir" / "config.toml"
        original = {
            "secrets": {"backend": "keychain"},
            "paths": {"crux_home": "/my/crux"},
        }
        save_config(original, path=config_file)
        assert config_file.exists()

        loaded = load_config(path=config_file)
        assert loaded["secrets"]["backend"] == "keychain"
        assert loaded["paths"]["crux_home"] == "/my/crux"

    def test_save_creates_parent_dirs(self, tmp_path):
        config_file = tmp_path / "a" / "b" / "config.toml"
        save_config({"secrets": {"backend": "plaintext"}}, path=config_file)
        assert config_file.exists()


class TestPlatformDetection:
    """detect_secrets_backend integrates with default_config."""

    def test_default_config_uses_platform_detection(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        cfg = default_config()
        # Should be one of the known backends
        assert cfg["secrets"]["backend"] in ("keychain", "secret-service", "plaintext")
