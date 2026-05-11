"""Tests for crux_cli.migrate_v1."""

from __future__ import annotations

import json

import pytest

from crux_cli import store
from crux_cli.bundle import load_bundle
from crux_cli.migrate_v1 import migrate_cwd
from crux_cli.pointer import read_pointer


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / "crux_home"))
    monkeypatch.delenv("CRUX_HOME", raising=False)


def test_migrate_basic(tmp_path):
    proj = tmp_path / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"name": "myproj", "mcps": ["fs"], "skills": ["s"]}))
    migrate_cwd(proj)
    assert not (proj / "crux.json").exists()
    assert (proj / "crux.toml").exists()
    assert read_pointer(proj / "crux.toml") == ("myproj", "v1")
    assert store.harness_versions("myproj") == ["v1"]
    b = load_bundle(store.harness_dir("myproj", "v1"))
    assert b["mcps"]["include"] == ["fs"]
    assert b["skills"]["include"] == ["s"]


def test_migrate_with_explicit_name(tmp_path):
    proj = tmp_path / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"mcps": [], "skills": []}))
    migrate_cwd(proj, name="custom")
    assert read_pointer(proj / "crux.toml") == ("custom", "v1")


def test_migrate_falls_back_to_dirname(tmp_path):
    proj = tmp_path / "fallback-dir"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"mcps": [], "skills": []}))
    migrate_cwd(proj)
    assert "fallback-dir" in store.list_harnesses()


def test_migrate_collision(tmp_path):
    from crux_cli.harness_ops import new_harness

    new_harness("myproj")
    proj = tmp_path / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"name": "myproj", "mcps": [], "skills": []}))
    with pytest.raises(FileExistsError):
        migrate_cwd(proj)


def test_migrate_no_crux_json(tmp_path):
    with pytest.raises(FileNotFoundError):
        migrate_cwd(tmp_path)
