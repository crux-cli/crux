"""Integration tests: crux sync"""
import json

import pytest

from .conftest import run_crux


def _make_project(root, name, mcps=None, skills=None):
    project = root / "src" / name
    project.mkdir(parents=True, exist_ok=True)
    crux_json = {"name": name, "version": "0.1.0", "mcps": mcps or [], "skills": skills or []}
    (project / "crux.json").write_text(json.dumps(crux_json))
    return project


@pytest.mark.integration
class TestCruxSync:
    def test_generates_mcp_json_for_project(self, crux_env):
        env, root = crux_env
        project = _make_project(root, "proj1", mcps=["memory"])
        result = run_crux("sync", env=env, cwd=str(project))
        assert result.returncode == 0, result.stdout
        mcp_json_path = project / ".mcp.json"
        assert mcp_json_path.exists()
        data = json.loads(mcp_json_path.read_text())
        assert "memory" in data["mcpServers"]

    def test_mcp_json_has_command_field(self, crux_env):
        env, root = crux_env
        project = _make_project(root, "proj1", mcps=["memory"])
        run_crux("sync", env=env, cwd=str(project))
        data = json.loads((project / ".mcp.json").read_text())
        assert "command" in data["mcpServers"]["memory"]

    def test_reports_unknown_mcp(self, crux_env):
        env, root = crux_env
        project = _make_project(root, "proj1", mcps=["nonexistent-mcp"])
        result = run_crux("sync", env=env, cwd=str(project))
        assert "nonexistent-mcp" in result.stdout

    def test_syncs_all_tracked_projects(self, crux_env):
        """crux sync --all syncs all registered projects."""
        env, root = crux_env
        p1 = _make_project(root, "proj1", mcps=["memory"])
        p2 = _make_project(root, "proj2", mcps=["memory"])
        # Register them via crux init (which writes to projects.json)
        run_crux("init", env=env, cwd=str(p1))
        run_crux("init", env=env, cwd=str(p2))
        # Now sync --all should work (but projects already have crux.json so init will fail)
        # Instead, register them manually
        projects_data = {
            "projects": [
                {"path": str(p1), "name": "proj1", "registered_at": "2026-01-01"},
                {"path": str(p2), "name": "proj2", "registered_at": "2026-01-01"},
            ]
        }
        (root / "projects.json").write_text(json.dumps(projects_data))
        result = run_crux("sync", "--all", env=env)
        assert result.returncode == 0, result.stdout
        assert "2 synced" in result.stdout

    def test_no_crux_json_exits_nonzero(self, crux_env):
        env, root = crux_env
        empty_dir = root / "emptydir"
        empty_dir.mkdir()
        result = run_crux("sync", env=env, cwd=str(empty_dir))
        assert result.returncode != 0

    def test_no_projects_shows_message(self, crux_env):
        env, root = crux_env
        empty_dir = root / "emptydir"
        empty_dir.mkdir()
        result = run_crux("sync", env=env, cwd=str(empty_dir))
        assert "No crux.json" in result.stdout or "no" in result.stdout.lower()
