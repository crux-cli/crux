"""Integration tests: crux skill add/remove/list"""

import json

import pytest

from .conftest import run_crux


def _load_registry(root):
    reg_path = root / "registry.json"
    with open(reg_path) as f:
        return json.load(f)


@pytest.mark.integration
class TestSkillList:
    def test_list_returns_zero(self, crux_env):
        env, root = crux_env
        result = run_crux("skill", "list", env=env)
        assert result.returncode == 0

    def test_list_json(self, crux_env):
        env, root = crux_env
        result = run_crux("skill", "list", "--json", env=env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "skill_definitions" in data


@pytest.mark.integration
class TestSkillRemove:
    def test_remove_nonexistent_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("skill", "remove", "nope", env=env)
        assert result.returncode != 0
