"""Tests for crux_cli.paths — Crux home directory path resolution."""

from pathlib import Path

from crux_cli.paths import (
    config_path,
    crux_home,
    launchers_dir,
    mcps_dir,
    projects_path,
    registry_path,
    sandbox_dir,
    secrets_path,
    skills_dir,
)


class TestCruxHome:
    """Tests for crux_home() resolution."""

    def test_default_is_dot_crux(self, monkeypatch):
        monkeypatch.delenv("CRUX_HOME", raising=False)
        monkeypatch.delenv("CRUX_TEST_ROOT", raising=False)
        result = crux_home()
        assert result == Path.home() / ".crux"

    def test_crux_home_env_override(self, monkeypatch):
        monkeypatch.delenv("CRUX_TEST_ROOT", raising=False)
        monkeypatch.setenv("CRUX_HOME", "/custom/crux")
        assert crux_home() == Path("/custom/crux")

    def test_crux_test_root_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("CRUX_HOME", "/custom/crux")
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/test-root")
        assert crux_home() == Path("/tmp/test-root")

    def test_crux_test_root_without_crux_home(self, monkeypatch):
        monkeypatch.delenv("CRUX_HOME", raising=False)
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/test-root")
        assert crux_home() == Path("/tmp/test-root")


class TestPathConstants:
    """All path helpers should return paths under crux_home()."""

    def test_registry_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert registry_path() == Path("/tmp/fx/registry.json")

    def test_mcps_dir(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert mcps_dir() == Path("/tmp/fx/mcps")

    def test_launchers_dir(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert launchers_dir() == Path("/tmp/fx/mcps/launchers")

    def test_skills_dir(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert skills_dir() == Path("/tmp/fx/skills")

    def test_sandbox_dir(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert sandbox_dir() == Path("/tmp/fx/sandbox")

    def test_projects_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert projects_path() == Path("/tmp/fx/projects.json")

    def test_secrets_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert secrets_path() == Path("/tmp/fx/secrets.json")

    def test_config_path(self, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", "/tmp/fx")
        monkeypatch.delenv("CRUX_HOME", raising=False)
        assert config_path() == Path("/tmp/fx/config.toml")


class TestTestIsolation:
    """CRUX_TEST_ROOT should fully isolate all paths."""

    def test_all_paths_under_test_root(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        paths = [
            crux_home(),
            registry_path(),
            mcps_dir(),
            launchers_dir(),
            skills_dir(),
            sandbox_dir(),
            projects_path(),
            secrets_path(),
            config_path(),
        ]
        for p in paths:
            assert str(p).startswith(str(tmp_path)), f"{p} is not under {tmp_path}"
