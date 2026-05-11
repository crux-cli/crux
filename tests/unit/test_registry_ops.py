"""Tests for crux_cli.registry_ops."""

from __future__ import annotations

import pytest

from crux_cli import store
from crux_cli.bundle import load_bundle, save_bundle
from crux_cli.harness_ops import new_harness
from crux_cli.registry_ops import (
    add_mcp,
    add_plugin_local,
    add_skill_local,
    remove,
)


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)
    # Avoid actually invoking npm / uv.
    monkeypatch.setattr("crux_cli.registry_ops.install_npm_package", lambda p: (True, ""))
    monkeypatch.setattr("crux_cli.registry_ops.install_uv_package", lambda p: (True, ""))


def test_add_mcp_npm(tmp_path):
    add_mcp("fs", source_kind="npm", source="@x/fs", skip_install=False)
    data = store.load_mcp_entry("fs")
    assert data["type"] == "npm"
    assert data["command"] == "npx"
    assert "@x/fs" in data["args"]


def test_add_mcp_uvx(tmp_path):
    add_mcp("py", source_kind="uvx", source="mcp-server-py")
    data = store.load_mcp_entry("py")
    assert data["type"] == "uvx"
    assert data["command"] == "uvx"
    assert data["args"][0] == "mcp-server-py"


def test_add_mcp_with_keychain(tmp_path):
    add_mcp("wikijs", source_kind="npm", source="wikijs-mcp", keychain=["API_KEY"])
    data = store.load_mcp_entry("wikijs")
    assert data["auth"]["type"] == "keychain"
    assert data["auth"]["env_vars"] == ["API_KEY"]


def test_add_mcp_local(tmp_path):
    add_mcp("custom", source_kind="local", source="/opt/myapp")
    data = store.load_mcp_entry("custom")
    assert data["source_dir"] == "/opt/myapp"


def test_add_mcp_http(tmp_path):
    add_mcp("remote", source_kind="http", source="https://example.com/mcp")
    data = store.load_mcp_entry("remote")
    assert data["url"] == "https://example.com/mcp"


def test_add_mcp_collision(tmp_path):
    add_mcp("fs", source_kind="npm", source="x")
    with pytest.raises(FileExistsError):
        add_mcp("fs", source_kind="npm", source="x")


def test_add_skill_local(tmp_path):
    src = tmp_path / "myskill"
    src.mkdir()
    (src / "SKILL.md").write_text("hello")
    add_skill_local("myskill", src)
    assert "myskill" in store.list_skills()
    assert (store.skill_dir("myskill") / "SKILL.md").exists()


def test_add_skill_local_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        add_skill_local("x", tmp_path / "nope")


def test_add_plugin_local(tmp_path):
    src = tmp_path / "p"
    src.mkdir()
    (src / "plugin.toml").write_text("hello")
    add_plugin_local("p", src, version="v1")
    assert store.plugin_versions("p") == ["v1"]


def test_remove_unreferenced(tmp_path):
    add_mcp("fs", source_kind="npm", source="x")
    remove("fs", force=False)
    assert "fs" not in store.list_mcps()


def test_remove_referenced_requires_force(tmp_path):
    add_mcp("fs", source_kind="npm", source="x")
    hdir = new_harness("h")
    b = load_bundle(hdir)
    b["mcps"]["include"] = ["fs"]
    save_bundle(hdir, b)
    with pytest.raises(RuntimeError):
        remove("fs", force=False)
    remove("fs", force=True)
    assert "fs" not in store.list_mcps()


def test_remove_unknown_name(tmp_path):
    with pytest.raises(FileNotFoundError):
        remove("nope", force=False)
