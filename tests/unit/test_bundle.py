"""Tests for crux_cli.bundle."""

from __future__ import annotations

from pathlib import Path

from crux_cli.bundle import default_bundle, load_bundle, save_bundle


def test_default_bundle_roundtrips(tmp_path: Path):
    save_bundle(tmp_path, default_bundle("foo", "v1"))
    b = load_bundle(tmp_path)
    assert b["harness"]["name"] == "foo"
    assert b["harness"]["version"] == "v1"
    assert b["skills"]["include"] == []
    assert b["mcps"]["include"] == []
    assert b["plugins"]["include"] == []


def test_default_bundle_description(tmp_path: Path):
    save_bundle(tmp_path, default_bundle("foo", "v2", "a tuned harness"))
    b = load_bundle(tmp_path)
    assert b["harness"]["description"] == "a tuned harness"


def test_add_remove_includes(tmp_path: Path):
    save_bundle(tmp_path, default_bundle("x", "v1"))
    b = load_bundle(tmp_path)
    b["skills"]["include"].extend(["a", "b"])
    b["mcps"]["include"].append("fs")
    save_bundle(tmp_path, b)
    reloaded = load_bundle(tmp_path)
    assert reloaded["skills"]["include"] == ["a", "b"]
    assert reloaded["mcps"]["include"] == ["fs"]


def test_load_fills_defaults_for_partial_file(tmp_path: Path):
    (tmp_path / "bundle.toml").write_text('[harness]\nname = "x"\nversion = "v1"\n')
    b = load_bundle(tmp_path)
    assert b["skills"]["include"] == []
    assert b["plugins"]["include"] == []
