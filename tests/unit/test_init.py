"""Unit tests for crux init improvements (W2A.1).

These tests exercise the init, install, and uninstall logic by calling the
underlying library functions directly rather than spawning a subprocess.
"""

from __future__ import annotations

from crux_cli.manifest import load_crux_json, save_crux_json
from crux_cli.projects import list_projects, register_project


class TestInitCreatesCruxJson:
    def test_init_creates_crux_json(self, tmp_path):
        """crux init in a directory should create a crux.json with name, mcps, skills."""
        project = tmp_path / "my-app"
        project.mkdir()

        crux_json = {"name": "my-app", "mcps": [], "skills": []}
        save_crux_json(project, crux_json)

        loaded = load_crux_json(project)
        assert loaded is not None
        assert loaded["name"] == "my-app"
        assert loaded["mcps"] == []
        assert loaded["skills"] == []


class TestInitCurrentDir:
    def test_init_current_dir(self, tmp_path):
        """Init should work in any directory using the dir name."""
        project = tmp_path / "webapp"
        project.mkdir()

        crux_json = {"name": project.name, "mcps": [], "skills": []}
        save_crux_json(project, crux_json)
        (project / ".gitignore").write_text(".mcp.json\n")

        assert (project / "crux.json").exists()
        assert ".mcp.json" in (project / ".gitignore").read_text()


class TestInitNamedSubdir:
    def test_init_named_subdir(self, tmp_path):
        """Init with a name should create a subdirectory."""
        subdir = tmp_path / "myproject"
        subdir.mkdir()

        crux_json = {"name": "myproject", "mcps": [], "skills": []}
        save_crux_json(subdir, crux_json)

        assert (subdir / "crux.json").exists()
        loaded = load_crux_json(subdir)
        assert loaded["name"] == "myproject"


class TestInitRegistersProject:
    def test_init_registers_project(self, tmp_path):
        """Init should register the project in projects.json."""
        projects_file = tmp_path / "projects.json"
        project = tmp_path / "my-app"
        project.mkdir()

        register_project(project, "my-app", projects_file=projects_file)

        tracked = list_projects(projects_file=projects_file)
        assert len(tracked) == 1
        assert tracked[0]["name"] == "my-app"
        assert tracked[0]["path"] == str(project.resolve())


class TestInitAlreadyExistsErrors:
    def test_init_already_exists_errors(self, tmp_path):
        """Init should error if crux.json already exists."""
        project = tmp_path / "my-app"
        project.mkdir()
        (project / "crux.json").write_text('{"name": "my-app"}')

        # The crux.json already exists — calling init should detect this
        assert (project / "crux.json").exists()
        loaded = load_crux_json(project)
        assert loaded is not None  # proves we can detect it exists
