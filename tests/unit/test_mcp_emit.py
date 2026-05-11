"""Tests for crux_cli.mcp_emit."""

from __future__ import annotations

import json

import pytest

from crux_cli import paths, store
from crux_cli.bundle import default_bundle, save_bundle
from crux_cli.mcp_emit import emit_mcp_json


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.delenv("CRUX_HOME", raising=False)


def test_emit_npm_mcp(tmp_path):
    store.save_mcp_entry("fs", {"type": "npm", "command": "npx", "args": ["-y", "@x/fs"]})
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1")
    b["mcps"]["include"] = ["fs"]
    save_bundle(hdir, b)
    out = tmp_path / ".mcp.json"
    emit_mcp_json("h", "v1", out_path=out)
    data = json.loads(out.read_text())
    assert data["mcpServers"]["fs"]["command"] == "npx"
    assert data["mcpServers"]["fs"]["args"] == ["-y", "@x/fs"]


def test_emit_keychain_wrapped(tmp_path):
    store.save_mcp_entry(
        "wikijs",
        {
            "type": "npm",
            "command": "npx",
            "args": ["-y", "wikijs-mcp"],
            "auth": {"type": "keychain", "env_vars": ["API_KEY"]},
        },
    )
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1")
    b["mcps"]["include"] = ["wikijs"]
    save_bundle(hdir, b)
    out = tmp_path / ".mcp.json"
    emit_mcp_json("h", "v1", out_path=out)
    data = json.loads(out.read_text())
    e = data["mcpServers"]["wikijs"]
    assert e["env"]["CRUX_MCP_NAME"] == "wikijs"
    assert e["env"]["CRUX_AUTH_ENV_VARS"] == "API_KEY"
    assert e["command"].endswith("keychain-auth.sh")
    assert e["args"][0] == "npx"


def test_emit_http_bearer(tmp_path):
    store.save_mcp_entry(
        "remote",
        {
            "type": "http",
            "url": "https://example.com/mcp",
            "auth": {"type": "bearer", "keychain_key": "API_TOKEN"},
        },
    )
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1")
    b["mcps"]["include"] = ["remote"]
    save_bundle(hdir, b)
    out = tmp_path / ".mcp.json"
    emit_mcp_json("h", "v1", out_path=out)
    data = json.loads(out.read_text())
    e = data["mcpServers"]["remote"]
    assert e["command"].endswith("http-bridge-auth.sh")
    assert e["env"]["CRUX_BRIDGE_URL"] == "https://example.com/mcp"
    assert e["env"]["CRUX_AUTH_KEYCHAIN_KEY"] == "API_TOKEN"


def test_emit_empty_bundle(tmp_path):
    hdir = paths.harnesses_root() / "h" / "v1"
    save_bundle(hdir, default_bundle("h", "v1"))
    out = tmp_path / ".mcp.json"
    emit_mcp_json("h", "v1", out_path=out)
    assert json.loads(out.read_text()) == {"mcpServers": {}}
