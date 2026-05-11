"""Shared fixtures for crux v2 tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def patch_secrets_paths(monkeypatch, tmp_path):
    """Redirect secrets module paths to a temp dir."""
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))


@pytest.fixture
def mock_keychain(mocker):
    """Mock macOS ``security`` binary calls so keychain tests run on any platform.

    Returns a dict simulating the keychain; tests can inspect or mutate it.
    """
    store: dict[tuple[str, str], str] = {}

    def fake_run(cmd, **_kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stderr = b""
        result.stdout = ""

        if "add-generic-password" in cmd:
            svc = cmd[cmd.index("-s") + 1]
            account = cmd[cmd.index("-a") + 1]
            val = cmd[cmd.index("-w") + 1]
            store[(svc, account)] = val
        elif "find-generic-password" in cmd:
            svc = cmd[cmd.index("-s") + 1]
            account = cmd[cmd.index("-a") + 1]
            val = store.get((svc, account))
            if val:
                result.stdout = val + "\n"
            else:
                result.returncode = 44
        elif "delete-generic-password" in cmd:
            svc = cmd[cmd.index("-s") + 1]
            account = cmd[cmd.index("-a") + 1]
            store.pop((svc, account), None)

        return result

    mocker.patch("crux_cli.secrets.subprocess.run", side_effect=fake_run)
    return store
