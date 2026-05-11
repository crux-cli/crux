"""Tests for crux_cli.harness_ops."""

from __future__ import annotations

import pytest

from crux_cli import store
from crux_cli.bundle import load_bundle
from crux_cli.harness_ops import bump, new_harness


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)


def test_new_creates_v1(tmp_path):
    hdir = new_harness("foo")
    assert hdir.name == "v1"
    assert (hdir / "bundle.toml").exists()
    assert (hdir / "CLAUDE.md").exists()
    assert (hdir / "hooks").is_dir()


def test_new_collides(tmp_path):
    new_harness("foo")
    with pytest.raises(FileExistsError):
        new_harness("foo")


def test_bump_copies_latest(tmp_path):
    hdir = new_harness("foo")
    (hdir / "CLAUDE.md").write_text("hi v1\n")
    nxt = bump("foo")
    assert nxt.name == "v2"
    assert (nxt / "CLAUDE.md").read_text() == "hi v1\n"
    assert store.harness_versions("foo") == ["v1", "v2"]
    assert load_bundle(nxt)["harness"]["version"] == "v2"


def test_bump_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        bump("nope")


def test_bump_preserves_includes(tmp_path):
    from crux_cli.bundle import save_bundle

    hdir = new_harness("h")
    b = load_bundle(hdir)
    b["skills"]["include"] = ["s1", "s2"]
    b["mcps"]["include"] = ["fs"]
    save_bundle(hdir, b)
    nxt = bump("h")
    nb = load_bundle(nxt)
    assert nb["skills"]["include"] == ["s1", "s2"]
    assert nb["mcps"]["include"] == ["fs"]
