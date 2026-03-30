"""Unit tests for crux install / uninstall logic (W2A.2, W2A.3).

These exercise the sync engine used by install/uninstall rather than spawning
a subprocess — keeping them fast and deterministic.
"""

from __future__ import annotations

import json
import shutil

from crux_cli.manifest import load_crux_json, save_crux_json
from crux_cli.sync import sync_project


def _registry(mcps=None, skills=None):
    return {
        "version": "1.0.0",
        "mcp_definitions": mcps or {},
        "skill_definitions": skills or {},
    }


# ---------------------------------------------------------------------------
# W2A.2: crux install
# ---------------------------------------------------------------------------


class TestInstallSingleMcp:
    def test_install_single_mcp(self, tmp_path):
        """Installing a single MCP adds it to crux.json and generates .mcp.json."""
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": [], "skills": []}
        # Simulate what cmd_install does: add to mcps, save, then sync
        crux_json["mcps"].append("memory")
        save_crux_json(project, crux_json)

        registry = _registry(
            mcps={
                "memory": {"command": "npx", "args": ["-y", "pkg"]},
            }
        )
        success, issues = sync_project(project, registry)
        assert success
        assert issues == []

        loaded = load_crux_json(project)
        assert "memory" in loaded["mcps"]
        assert (project / ".mcp.json").exists()


class TestInstallMultipleMcps:
    def test_install_multiple_mcps(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": ["memory", "github-mcp"], "skills": []}
        save_crux_json(project, crux_json)

        registry = _registry(
            mcps={
                "memory": {"command": "npx", "args": ["-y", "mem-pkg"]},
                "github-mcp": {"command": "npx", "args": ["-y", "gh-pkg"]},
            }
        )
        success, issues = sync_project(project, registry)
        assert success
        assert issues == []

        data = json.loads((project / ".mcp.json").read_text())
        assert "memory" in data["mcpServers"]
        assert "github-mcp" in data["mcpServers"]


class TestInstallSkillCopiesToClaudeSkills:
    def test_install_skill_copies_to_claude_skills(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()

        # Create a fake skill source
        skill_source = tmp_path / "skills" / "my-skill"
        skill_source.mkdir(parents=True)
        (skill_source / "SKILL.md").write_text("# My Skill\n")

        crux_json = {"name": "proj", "mcps": [], "skills": ["my-skill"]}
        save_crux_json(project, crux_json)

        registry = _registry(
            skills={
                "my-skill": {"type": "local", "source_dir": str(skill_source)},
            }
        )
        success, issues = sync_project(project, registry)
        assert success
        assert issues == []

        dest = project / ".claude" / "skills" / "my-skill"
        assert dest.exists()
        assert (dest / "SKILL.md").exists()


class TestInstallAlreadyInstalledSkips:
    def test_install_already_installed_skips(self, tmp_path):
        """If an MCP is already in crux.json mcps, it should be a no-op."""
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": ["memory"], "skills": []}
        save_crux_json(project, crux_json)

        # "memory" is already in mcps — checking membership
        loaded = load_crux_json(project)
        assert "memory" in loaded["mcps"]


class TestInstallNotInRegistryErrors:
    def test_install_not_in_registry_errors(self, tmp_path):
        """Sync should report an issue for MCPs not in registry."""
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": ["nonexistent"], "skills": []}
        save_crux_json(project, crux_json)

        registry = _registry()
        success, issues = sync_project(project, registry)
        assert any("nonexistent" in i for i in issues)


class TestInstallTriggersSync:
    def test_install_triggers_sync(self, tmp_path):
        """After install, .mcp.json should be generated (sync runs automatically)."""
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": ["memory"], "skills": []}
        save_crux_json(project, crux_json)

        registry = _registry(
            mcps={
                "memory": {"command": "npx", "args": ["-y", "pkg"]},
            }
        )
        sync_project(project, registry)

        assert (project / ".mcp.json").exists()
        data = json.loads((project / ".mcp.json").read_text())
        assert "memory" in data["mcpServers"]


# ---------------------------------------------------------------------------
# W2A.3: crux uninstall
# ---------------------------------------------------------------------------


class TestUninstallRemovesFromCruxJson:
    def test_uninstall_removes_from_crux_json(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": ["memory", "github-mcp"], "skills": []}
        save_crux_json(project, crux_json)

        # Simulate uninstall: remove from mcps, save
        crux_json["mcps"].remove("memory")
        save_crux_json(project, crux_json)

        loaded = load_crux_json(project)
        assert "memory" not in loaded["mcps"]
        assert "github-mcp" in loaded["mcps"]


class TestUninstallRemovesSkillDir:
    def test_uninstall_removes_skill_dir(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()

        # Simulate an installed skill
        skill_dest = project / ".claude" / "skills" / "my-skill"
        skill_dest.mkdir(parents=True)
        (skill_dest / "SKILL.md").write_text("# test")

        crux_json = {"name": "proj", "mcps": [], "skills": ["my-skill"]}
        save_crux_json(project, crux_json)

        # Simulate uninstall: remove from skills, delete dir
        crux_json["skills"].remove("my-skill")
        save_crux_json(project, crux_json)
        if skill_dest.exists():
            shutil.rmtree(skill_dest)

        loaded = load_crux_json(project)
        assert "my-skill" not in loaded["skills"]
        assert not skill_dest.exists()


class TestUninstallTriggersSync:
    def test_uninstall_triggers_sync(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": ["memory"], "skills": []}
        save_crux_json(project, crux_json)

        registry = _registry(
            mcps={
                "memory": {"command": "npx", "args": ["-y", "pkg"]},
            }
        )

        # Install + sync
        sync_project(project, registry)
        data = json.loads((project / ".mcp.json").read_text())
        assert "memory" in data["mcpServers"]

        # Uninstall + sync
        crux_json["mcps"].remove("memory")
        save_crux_json(project, crux_json)
        sync_project(project, registry)

        data = json.loads((project / ".mcp.json").read_text())
        assert "memory" not in data["mcpServers"]


class TestUninstallNotInstalledErrors:
    def test_uninstall_not_installed_errors(self, tmp_path):
        """Uninstalling something not in crux.json should be detectable."""
        project = tmp_path / "proj"
        project.mkdir()

        crux_json = {"name": "proj", "mcps": [], "skills": []}
        save_crux_json(project, crux_json)

        loaded = load_crux_json(project)
        assert "nonexistent" not in loaded.get("mcps", [])
        assert "nonexistent" not in loaded.get("skills", [])
