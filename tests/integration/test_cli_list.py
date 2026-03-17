"""Integration tests: crux list"""
import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestCruxList:
    def test_shows_mcp_names(self, crux_env):
        env, _ = crux_env
        result = run_crux("list", env=env)
        assert result.returncode == 0
        assert "memory" in result.stdout
        assert "wikijs-mcp" in result.stdout
        assert "github-mcp" in result.stdout

    def test_shows_skill_names(self, crux_env):
        env, _ = crux_env
        result = run_crux("list", env=env)
        assert "claude-xlsx" in result.stdout

    def test_shows_mcp_type(self, crux_env):
        env, _ = crux_env
        result = run_crux("list", env=env)
        assert "npm-package" in result.stdout
        assert "git-submodule" in result.stdout

    def test_shows_tags(self, crux_env):
        env, _ = crux_env
        result = run_crux("list", env=env)
        assert "memory" in result.stdout
        assert "wiki" in result.stdout

    def test_exits_zero(self, crux_env):
        env, _ = crux_env
        result = run_crux("list", env=env)
        assert result.returncode == 0
