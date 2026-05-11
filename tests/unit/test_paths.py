"""Tests for crux_cli.paths — base resolution helpers."""

from __future__ import annotations

from pathlib import Path

from crux_cli.paths import config_path, crux_home, secrets_path, tokens_path


class TestCruxHome:
    def test_default_is_dot_crux(self, monkeypatch):
        monkeypatch.delenv("CRUX_HOME", raising=False)
        monkeypatch.delenv("CRUX_TEST_ROOT", raising=False)
        assert crux_home() == Path.home() / ".crux"

    def test_crux_home_env_override(self, monkeypatch):
        monkeypatch.delenv("CRUX_TEST_ROOT", raising=False)
        monkeypatch.setenv("CRUX_HOME", "/custom/crux")
        assert crux_home() == Path("/custom/crux")

    def test_crux_test_root_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("CRUX_HOME", "/custom/crux")
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/test-root")
        assert crux_home() == Path("/tmp/test-root")


class TestPathConstants:
    def test_secrets_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert secrets_path() == Path("/tmp/fx/secrets.json")

    def test_config_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert config_path() == Path("/tmp/fx/config.toml")

    def test_tokens_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert tokens_path() == Path("/tmp/fx/tokens.json")
