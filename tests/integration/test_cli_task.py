"""Integration tests: crux task init/list/clean"""

import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestTaskInit:
    def test_init_creates_run_json(self, crux_env):
        env, root = crux_env
        workdir = root / "tasktest"
        workdir.mkdir()
        result = run_crux("task", "init", "my-task", env=env, cwd=str(workdir))
        assert result.returncode == 0
        assert (workdir / "run.json").exists()

    def test_init_fails_if_exists(self, crux_env):
        env, root = crux_env
        workdir = root / "tasktest2"
        workdir.mkdir()
        (workdir / "run.json").write_text("{}")
        result = run_crux("task", "init", env=env, cwd=str(workdir))
        assert result.returncode != 0


@pytest.mark.integration
class TestTaskList:
    def test_list_empty(self, crux_env):
        env, root = crux_env
        result = run_crux("task", "list", env=env)
        assert result.returncode == 0


@pytest.mark.integration
class TestTaskClean:
    def test_clean_empty(self, crux_env):
        env, root = crux_env
        result = run_crux("task", "clean", "--force", env=env)
        assert result.returncode == 0
