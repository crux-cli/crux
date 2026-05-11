"""Tests for crux_cli.paths v2 helpers (registry tree, pointers, claude dirs)."""

from __future__ import annotations

from crux_cli import paths


def test_registry_subpaths(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)
    assert paths.registry_root() == tmp_path / "registry"
    assert paths.mcps_root() == tmp_path / "registry" / "mcps"
    assert paths.skills_root() == tmp_path / "registry" / "skills"
    assert paths.plugins_root() == tmp_path / "registry" / "plugins"
    assert paths.harnesses_root() == tmp_path / "registry" / "harnesses"
    assert paths.active_pointer_path() == tmp_path / "active.toml"
    assert paths.history_path() == tmp_path / "history"


def test_claude_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert paths.claude_user_dir() == tmp_path / ".claude"
    assert paths.claude_dir_for(tmp_path / "proj") == tmp_path / "proj" / ".claude"
