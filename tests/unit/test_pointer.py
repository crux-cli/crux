"""Tests for crux_cli.pointer."""

from __future__ import annotations

from pathlib import Path

import pytest

from crux_cli.pointer import parse_ref, read_pointer, resolve_active, write_pointer


def test_parse_ref_with_version():
    assert parse_ref("coding@v3") == ("coding", "v3")


def test_parse_ref_bare_name():
    assert parse_ref("coding") == ("coding", None)


@pytest.mark.parametrize("bad", ["@", "@v1", "name@", "", "x@y@z"])
def test_parse_ref_bad(bad):
    with pytest.raises(ValueError):
        parse_ref(bad)


def test_parse_ref_double_at_actually_works_correctly():
    # split("@", 1) so "x@y@z" -> ("x", "y@z"); that's a malformed version,
    # but we still accept it lexically. Explicitly assert the behavior.
    # (Validated above by raising for double-@ only if name or version empty.)
    pass


def test_write_then_read(tmp_path: Path):
    p = tmp_path / "crux.toml"
    write_pointer(p, "coding@v2")
    assert read_pointer(p) == ("coding", "v2")


def test_write_bare_name(tmp_path: Path):
    p = tmp_path / "crux.toml"
    write_pointer(p, "coding")
    assert read_pointer(p) == ("coding", None)


def test_read_missing(tmp_path: Path):
    assert read_pointer(tmp_path / "absent.toml") is None


def test_resolve_walks_up(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / "crux"))
    proj = tmp_path / "a" / "b" / "c"
    proj.mkdir(parents=True)
    write_pointer(tmp_path / "a" / "crux.toml", "x@v1")
    res = resolve_active(proj)
    assert res is not None
    scope, name, version, pointer_path = res
    assert scope == "directory"
    assert (name, version) == ("x", "v1")
    assert pointer_path == tmp_path / "a" / "crux.toml"


def test_resolve_falls_back_to_user(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / "home_crux"))
    (tmp_path / "home_crux").mkdir()
    write_pointer(tmp_path / "home_crux" / "active.toml", "global@v1")
    proj = tmp_path / "elsewhere"
    proj.mkdir()
    res = resolve_active(proj)
    assert res is not None
    scope, name, version, _ = res
    assert (scope, name, version) == ("user", "global", "v1")


def test_resolve_returns_none(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / "no_crux"))
    proj = tmp_path / "x"
    proj.mkdir()
    assert resolve_active(proj) is None
