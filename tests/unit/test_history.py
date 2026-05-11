"""Tests for crux_cli.history."""

from __future__ import annotations

from pathlib import Path

from crux_cli.history import append, pop_previous, read_all


def test_append_and_pop(tmp_path: Path):
    h = tmp_path / "history"
    append(h, prev=None, new="a@v1")
    append(h, prev="a@v1", new="b@v2")
    assert pop_previous(h) == "a@v1"
    rows = read_all(h)
    assert len(rows) == 2


def test_pop_empty(tmp_path: Path):
    assert pop_previous(tmp_path / "nope") is None


def test_bounded_to_100(tmp_path: Path):
    h = tmp_path / "h"
    for i in range(120):
        append(h, prev=None, new=f"x@v{i}")
    rows = read_all(h)
    assert len(rows) == 100
    assert rows[-1][2] == "x@v119"


def test_pop_returns_none_when_no_previous(tmp_path: Path):
    h = tmp_path / "h"
    append(h, prev=None, new="first@v1")
    assert pop_previous(h) is None
