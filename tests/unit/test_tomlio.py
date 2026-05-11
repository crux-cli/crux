"""Tests for crux_cli.tomlio — minimal TOML reader/writer."""

from __future__ import annotations

import tomllib
from pathlib import Path

from crux_cli.tomlio import dump_toml, load_toml


def test_roundtrip_simple(tmp_path: Path):
    data = {"harness": "coding@v3"}
    p = tmp_path / "a.toml"
    dump_toml(p, data)
    assert load_toml(p) == data


def test_dump_tables_and_lists(tmp_path: Path):
    data = {
        "harness": {"name": "x", "version": "v2"},
        "skills": {"include": ["a", "b"]},
        "mcps": {"include": []},
    }
    p = tmp_path / "b.toml"
    dump_toml(p, data)
    assert load_toml(p) == data


def test_dump_atomic_no_leftover(tmp_path: Path):
    p = tmp_path / "c.toml"
    p.write_text('harness = "old"\n')
    dump_toml(p, {"harness": "new"})
    assert tomllib.loads(p.read_text())["harness"] == "new"
    assert [x.name for x in tmp_path.iterdir()] == ["c.toml"]


def test_string_with_quote(tmp_path: Path):
    p = tmp_path / "d.toml"
    dump_toml(p, {"desc": 'hello "world"'})
    assert load_toml(p) == {"desc": 'hello "world"'}


def test_bool_and_int(tmp_path: Path):
    p = tmp_path / "e.toml"
    dump_toml(p, {"enabled": True, "count": 3})
    assert load_toml(p) == {"enabled": True, "count": 3}
