"""Integration tests: crux run (init/list/clean subcommands; task execution mocked)."""
import json

import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestCruxRunInit:
    def test_creates_run_json(self, crux_env, tmp_path):
        env, root = crux_env
        result = run_crux("run", "init", "my-task", env=env, cwd=str(tmp_path))
        assert result.returncode == 0
        assert (tmp_path / "run.json").exists()

    def test_run_json_has_expected_fields(self, crux_env, tmp_path):
        env, root = crux_env
        run_crux("run", "init", "my-task", env=env, cwd=str(tmp_path))
        data = json.loads((tmp_path / "run.json").read_text())
        assert data["name"] == "my-task"
        assert "task" in data
        assert "mcps" in data
        assert "timeout" in data

    def test_fails_if_run_json_exists(self, crux_env, tmp_path):
        env, _ = crux_env
        (tmp_path / "run.json").write_text("{}")
        result = run_crux("run", "init", "my-task", env=env, cwd=str(tmp_path))
        assert result.returncode != 0
        assert "already exists" in result.stdout

    def test_shows_available_mcps(self, crux_env, tmp_path):
        env, _ = crux_env
        result = run_crux("run", "init", "my-task", env=env, cwd=str(tmp_path))
        assert "memory" in result.stdout


@pytest.mark.integration
class TestCruxRunList:
    def test_empty_sandbox_shows_no_runs(self, crux_env):
        env, _ = crux_env
        result = run_crux("run", "list", env=env)
        assert result.returncode == 0
        assert "No runs" in result.stdout

    def test_shows_run_from_meta_json(self, crux_env):
        env, root = crux_env
        sandbox_dir = root / "sandbox" / "20260315-abcd"
        sandbox_dir.mkdir(parents=True)
        meta = {
            "id": "20260315-abcd",
            "name": "test-run",
            "task": "List available tools",
            "mcps": ["memory"],
            "status": "done",
            "started_at": "2026-03-15T12:00:00",
        }
        (sandbox_dir / "run-meta.json").write_text(json.dumps(meta))
        result = run_crux("run", "list", env=env)
        assert result.returncode == 0
        assert "20260315-abcd" in result.stdout
        assert "test-run" in result.stdout


@pytest.mark.integration
class TestCruxRunClean:
    def test_force_cleans_all_sandboxes(self, crux_env):
        env, root = crux_env
        for name in ["sandbox1", "sandbox2"]:
            (root / "sandbox" / name).mkdir()
        result = run_crux("run", "clean", "--force", env=env)
        assert result.returncode == 0
        assert "2" in result.stdout
        assert not (root / "sandbox" / "sandbox1").exists()

    def test_empty_sandbox_reports_empty(self, crux_env):
        env, _ = crux_env
        result = run_crux("run", "clean", "--force", env=env)
        assert result.returncode == 0
        assert "empty" in result.stdout.lower()

    def test_force_removes_all(self, crux_env):
        env, root = crux_env
        (root / "sandbox" / "sandbox1").mkdir()
        (root / "sandbox" / "sandbox2").mkdir()
        result = run_crux("run", "clean", "--force", env=env)
        assert result.returncode == 0
        dirs = list((root / "sandbox").iterdir())
        assert len(dirs) == 0
