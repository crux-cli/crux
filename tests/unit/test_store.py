"""Tests for crux_cli.store."""

from __future__ import annotations

import pytest

from crux_cli import store
from crux_cli.bundle import default_bundle, save_bundle


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)


def test_list_harness_versions(tmp_path):
    save_bundle(tmp_path / "registry" / "harnesses" / "foo" / "v1", default_bundle("foo", "v1"))
    save_bundle(tmp_path / "registry" / "harnesses" / "foo" / "v2", default_bundle("foo", "v2"))
    save_bundle(tmp_path / "registry" / "harnesses" / "foo" / "v10", default_bundle("foo", "v10"))
    assert store.harness_versions("foo") == ["v1", "v2", "v10"]
    assert store.latest_version("foo") == "v10"
    assert store.next_version("foo") == "v11"


def test_next_version_starts_at_v1(tmp_path):
    assert store.next_version("nope") == "v1"


def test_list_harnesses_empty():
    assert store.list_harnesses() == []


def test_mcp_save_load(tmp_path):
    store.save_mcp_entry("filesystem", {"type": "npm", "command": "npx", "args": ["x"]})
    assert store.load_mcp_entry("filesystem") == {"type": "npm", "command": "npx", "args": ["x"]}
    assert "filesystem" in store.list_mcps()


def test_skill_dir(tmp_path):
    (tmp_path / "registry" / "skills" / "myskill").mkdir(parents=True)
    assert "myskill" in store.list_skills()
    assert store.skill_dir("myskill").name == "myskill"


def test_plugin_versions(tmp_path):
    (tmp_path / "registry" / "plugins" / "p" / "v1").mkdir(parents=True)
    (tmp_path / "registry" / "plugins" / "p" / "v2").mkdir(parents=True)
    assert store.plugin_versions("p") == ["v1", "v2"]
    assert store.plugin_dir("p").name == "v2"
    assert store.plugin_dir("p", "v1").name == "v1"


def test_harness_dir_with_latest(tmp_path):
    save_bundle(tmp_path / "registry" / "harnesses" / "h" / "v3", default_bundle("h", "v3"))
    assert store.harness_dir("h").name == "v3"
    assert store.harness_dir("h", "v3") == tmp_path / "registry" / "harnesses" / "h" / "v3"
