"""Integration tests: crux project sync"""

import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestProjectSync:
    def test_sync_no_crux_json_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("project", "sync", env=env, cwd=str(root))
        assert result.returncode != 0

    def test_sync_after_create(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "synctest", env=env, cwd=str(root))
        result = run_crux("project", "sync", env=env, cwd=str(root / "synctest"))
        assert result.returncode == 0

    def test_sync_all(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "p1", env=env, cwd=str(root))
        result = run_crux("project", "sync", "--all", env=env, cwd=str(root))
        assert result.returncode == 0
