"""Tests for crux_cli.setup (v2)."""

from __future__ import annotations

import pytest

from crux_cli import paths
from crux_cli.setup import run_setup


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)


def test_run_setup_creates_tree(tmp_path):
    res = run_setup()
    for d in [
        paths.crux_home(),
        paths.registry_root(),
        paths.mcps_root(),
        paths.skills_root(),
        paths.plugins_root(),
        paths.harnesses_root(),
        paths.crux_home() / "launchers",
    ]:
        assert d.exists()
    assert res.dirs_created


def test_run_setup_installs_skill(tmp_path):
    res = run_setup()
    assert res.skill_installed
    assert (paths.skills_root() / "crux" / "SKILL.md").exists()


def test_run_setup_installs_launchers(tmp_path):
    res = run_setup()
    assert "keychain-auth.sh" in res.launchers_installed
    assert "http-bridge-auth.sh" in res.launchers_installed
    launcher = paths.crux_home() / "launchers" / "keychain-auth.sh"
    assert launcher.exists()
    assert launcher.stat().st_mode & 0o111  # executable


def test_run_setup_writes_config(tmp_path):
    res = run_setup()
    assert res.config_written
    assert (paths.crux_home() / "config.toml").exists()


def test_run_setup_is_idempotent(tmp_path):
    run_setup()
    res = run_setup()
    # Second run shouldn't write the config again (no dirs created either)
    assert not res.config_written
    assert res.dirs_created == []
    # But the skill copy is still re-done (cheap, ensures it's up-to-date)
    assert res.skill_installed
