"""Integration tests: crux project create"""

import json

import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestProjectCreate:
    def test_creates_project_directory(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "myproject", env=env, cwd=str(root))
        assert (root / "myproject").is_dir()

    def test_creates_crux_json(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "myproject", env=env, cwd=str(root))
        crux_json_path = root / "myproject" / "crux.json"
        assert crux_json_path.exists()
        data = json.loads(crux_json_path.read_text())
        assert data["name"] == "myproject"
        assert "mcps" in data
        assert "skills" in data

    def test_creates_gitignore(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "myproject", env=env, cwd=str(root))
        gitignore = root / "myproject" / ".gitignore"
        assert gitignore.exists()
        assert ".mcp.json" in gitignore.read_text()

    def test_exits_nonzero_if_project_exists(self, crux_env):
        env, root = crux_env
        project = root / "existing"
        project.mkdir(parents=True)
        (project / "crux.json").write_text('{"name": "existing"}')
        result = run_crux("project", "create", "existing", env=env, cwd=str(root))
        assert result.returncode != 0
        assert "already exists" in result.stdout

    def test_success_message_shown(self, crux_env):
        env, root = crux_env
        result = run_crux("project", "create", "myproject", env=env, cwd=str(root))
        assert result.returncode == 0
        assert "myproject" in result.stdout

    def test_create_current_dir(self, crux_env):
        env, root = crux_env
        project = root / "my-app"
        project.mkdir()
        result = run_crux("project", "create", env=env, cwd=str(project))
        assert result.returncode == 0
        assert (project / "crux.json").exists()

    def test_create_with_mcp_flag(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "flagtest", "--mcp", "test-mcp", env=env, cwd=str(root))
        crux_json_path = root / "flagtest" / "crux.json"
        data = json.loads(crux_json_path.read_text())
        assert "test-mcp" in data["mcps"]

    def test_create_registers_project(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "tracked", env=env, cwd=str(root))
        projects_file = root / "projects.json"
        assert projects_file.exists()
