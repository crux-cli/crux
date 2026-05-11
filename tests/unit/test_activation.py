"""Tests for crux_cli.activation."""

from __future__ import annotations

import json

import pytest

from crux_cli import paths, store
from crux_cli.activation import ConflictError, activate, apply_plan, plan_symlinks
from crux_cli.bundle import default_bundle, save_bundle


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# plan_symlinks
# ---------------------------------------------------------------------------


def test_plan_includes_claude_md(tmp_path):
    hdir = paths.harnesses_root() / "h" / "v1"
    save_bundle(hdir, default_bundle("h", "v1"))
    (hdir / "CLAUDE.md").write_text("# h v1\n")
    plan = plan_symlinks("h", "v1", scope_target=tmp_path / "home" / ".claude")
    assert (tmp_path / "home" / ".claude" / "CLAUDE.md", hdir / "CLAUDE.md") in plan


def test_plan_includes_skills_plugins_hooks(tmp_path):
    (paths.skills_root() / "s").mkdir(parents=True)
    (paths.plugins_root() / "p" / "v2").mkdir(parents=True)
    hdir = paths.harnesses_root() / "h" / "v1"
    bundle = default_bundle("h", "v1")
    bundle["skills"]["include"] = ["s"]
    bundle["plugins"]["include"] = ["p@v2"]
    bundle["hooks"] = {"pre_tool_use": "hooks/pre.sh"}
    save_bundle(hdir, bundle)
    (hdir / "CLAUDE.md").write_text("# h\n")
    (hdir / "hooks").mkdir()
    (hdir / "hooks" / "pre.sh").write_text("#!/bin/sh\n")
    target = tmp_path / "home" / ".claude"
    plan = plan_symlinks("h", "v1", scope_target=target)
    sources = {src for _, src in plan}
    assert paths.skills_root() / "s" in sources
    assert paths.plugins_root() / "p" / "v2" in sources
    assert hdir / "hooks" / "pre.sh" in sources


# ---------------------------------------------------------------------------
# apply_plan
# ---------------------------------------------------------------------------


def test_apply_creates_links(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    target = tmp_path / "t" / "link"
    apply_plan([(target, src)], known_registry_root=tmp_path)
    assert target.is_symlink() and target.resolve() == src.resolve()


def test_apply_replaces_existing_managed_symlink(tmp_path):
    src_a = tmp_path / "registry" / "a"
    src_b = tmp_path / "registry" / "b"
    src_a.mkdir(parents=True)
    src_b.mkdir(parents=True)
    target = tmp_path / "t" / "link"
    apply_plan([(target, src_a)])
    apply_plan([(target, src_b)])
    assert target.resolve() == src_b.resolve()


def test_apply_rejects_regular_file(tmp_path):
    target = tmp_path / "t" / "link"
    target.parent.mkdir(parents=True)
    target.write_text("hello")
    with pytest.raises(ConflictError):
        apply_plan([(target, tmp_path / "registry" / "src")], known_registry_root=tmp_path / "registry")


def test_apply_rejects_foreign_symlink(tmp_path):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    target = tmp_path / "t" / "link"
    target.parent.mkdir(parents=True)
    target.symlink_to(foreign)
    with pytest.raises(ConflictError):
        apply_plan([(target, tmp_path / "registry" / "src")], known_registry_root=tmp_path / "registry")


# ---------------------------------------------------------------------------
# activate (end-to-end)
# ---------------------------------------------------------------------------


def test_activate_user_scope(tmp_path):
    store.save_mcp_entry("fs", {"type": "npm", "command": "npx", "args": ["-y", "@x/fs"]})
    (paths.skills_root() / "s").mkdir(parents=True)
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1")
    b["skills"]["include"] = ["s"]
    b["mcps"]["include"] = ["fs"]
    save_bundle(hdir, b)
    (hdir / "CLAUDE.md").write_text("# h\n")

    activate("h", "v1", scope="user", cwd=tmp_path)

    claude_home = tmp_path / "home" / ".claude"
    assert (claude_home / "CLAUDE.md").resolve() == (hdir / "CLAUDE.md").resolve()
    assert (claude_home / "skills" / "s").resolve() == (paths.skills_root() / "s").resolve()
    data = json.loads((claude_home / ".mcp.json").read_text())
    assert "fs" in data["mcpServers"]


def test_activate_replaces_previous(tmp_path):
    (paths.skills_root() / "s1").mkdir(parents=True)
    (paths.skills_root() / "s2").mkdir(parents=True)
    for v, skill in [("v1", "s1"), ("v2", "s2")]:
        hdir = paths.harnesses_root() / "h" / v
        b = default_bundle("h", v)
        b["skills"]["include"] = [skill]
        save_bundle(hdir, b)
        (hdir / "CLAUDE.md").write_text(f"# {v}\n")

    activate("h", "v1", scope="user", cwd=tmp_path)
    claude_home = tmp_path / "home" / ".claude"
    assert (claude_home / "skills" / "s1").exists()
    activate("h", "v2", scope="user", cwd=tmp_path)
    assert (claude_home / "skills" / "s2").exists()
    assert not (claude_home / "skills" / "s1").exists()


def test_activate_directory_scope(tmp_path):
    proj = tmp_path / "myproj"
    proj.mkdir()
    hdir = paths.harnesses_root() / "h" / "v1"
    save_bundle(hdir, default_bundle("h", "v1"))
    (hdir / "CLAUDE.md").write_text("# h\n")
    activate("h", "v1", scope="directory", cwd=proj)
    assert (proj / ".claude" / "CLAUDE.md").is_symlink()
