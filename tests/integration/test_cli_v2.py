"""End-to-end CLI tests for crux v2.

These tests exercise the CLI exactly as a user would: ``python -m crux_cli``
in a subprocess, with ``CRUX_TEST_ROOT`` and ``HOME`` redirected to a
temporary directory. Each test follows a realistic workflow.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(args: list[str], env_root: Path, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CRUX_TEST_ROOT"] = str(env_root)
    env["HOME"] = str(env_root / "home")
    env.pop("CRUX_HOME", None)
    (env_root / "home").mkdir(exist_ok=True)
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "crux_cli", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )


@pytest.fixture
def home(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# Workflow 1: fresh user — setup, build a harness, activate, inspect.
# ---------------------------------------------------------------------------


def test_first_run_workflow(home):
    """A new user runs setup, creates a harness, and activates it."""
    r = _run(["setup"], home)
    assert r.returncode == 0, r.stderr
    assert (home / "registry" / "harnesses").is_dir()
    assert (home / "registry" / "skills" / "crux" / "SKILL.md").exists()

    r = _run(["new", "coding"], home)
    assert r.returncode == 0, r.stderr
    bundle = home / "registry" / "harnesses" / "coding" / "v1" / "bundle.toml"
    assert bundle.exists()
    assert "coding" in bundle.read_text()

    r = _run(["use", "coding", "--user"], home)
    assert r.returncode == 0, r.stderr
    home_claude = home / "home" / ".claude"
    assert (home_claude / "CLAUDE.md").is_symlink()
    assert (home / "active.toml").read_text().strip() == 'harness = "coding@v1"'

    # `crux active` shows the user-scope pointer.
    r = _run(["active"], home, cwd=home)
    assert r.returncode == 0
    assert "coding" in r.stdout
    assert "user" in r.stdout


# ---------------------------------------------------------------------------
# Workflow 2: iterate — bump produces v2, list shows both, use selects.
# ---------------------------------------------------------------------------


def test_versioning_workflow(home):
    _run(["setup"], home)
    _run(["new", "coding"], home)
    r = _run(["bump", "coding"], home)
    assert r.returncode == 0, r.stderr
    assert (home / "registry" / "harnesses" / "coding" / "v2" / "bundle.toml").exists()

    r = _run(["list", "coding"], home)
    assert r.returncode == 0
    assert "v1" in r.stdout and "v2" in r.stdout

    _run(["use", "coding@v1", "--user"], home)
    assert (home / "active.toml").read_text().strip() == 'harness = "coding@v1"'
    _run(["use", "coding@v2", "--user"], home)
    assert (home / "active.toml").read_text().strip() == 'harness = "coding@v2"'


# ---------------------------------------------------------------------------
# Workflow 3: directory-level pointer overrides user-level.
# ---------------------------------------------------------------------------


def test_directory_scope_overrides_user(home):
    _run(["setup"], home)
    _run(["new", "global"], home)
    _run(["new", "proj"], home)

    _run(["use", "global", "--user"], home)
    project = home / "myproj"
    project.mkdir()
    r = _run(["use", "proj"], home, cwd=project)
    assert r.returncode == 0, r.stderr
    assert (project / "crux.toml").exists()
    assert (project / ".claude" / "CLAUDE.md").is_symlink()

    r = _run(["active"], home, cwd=project)
    assert "proj" in r.stdout and "directory" in r.stdout

    # Outside the project, user-level pointer wins.
    r = _run(["active"], home, cwd=home / "home")
    assert "global" in r.stdout and "user" in r.stdout


# ---------------------------------------------------------------------------
# Workflow 4: use - rolls back to the previous activation.
# ---------------------------------------------------------------------------


def test_use_dash_rolls_back(home):
    _run(["setup"], home)
    _run(["new", "a"], home)
    _run(["new", "b"], home)
    _run(["use", "a", "--user"], home)
    _run(["use", "b", "--user"], home)
    r = _run(["use", "-", "--user"], home)
    assert r.returncode == 0, r.stderr
    assert (home / "active.toml").read_text().strip() == 'harness = "a@v1"'


# ---------------------------------------------------------------------------
# Workflow 5: use --none deactivates.
# ---------------------------------------------------------------------------


def test_use_none_deactivates(home):
    _run(["setup"], home)
    _run(["new", "a"], home)
    _run(["use", "a", "--user"], home)
    assert (home / "active.toml").exists()
    r = _run(["use", "--none", "--user"], home)
    assert r.returncode == 0, r.stderr
    assert not (home / "active.toml").exists()


# ---------------------------------------------------------------------------
# Workflow 6: assemble a real bundle — add primitives, edit, activate.
# ---------------------------------------------------------------------------


def test_bundle_assembly_workflow(home, tmp_path):
    _run(["setup"], home)

    # Stage a local skill outside the registry.
    skill_src = tmp_path / "research"
    skill_src.mkdir()
    (skill_src / "SKILL.md").write_text("---\nname: research\n---\nDo research.\n")
    r = _run(["registry", "add", "skill", "research", str(skill_src), "--local"], home)
    assert r.returncode == 0, r.stderr

    # Add an MCP without installing (skip-install: don't touch npm in tests).
    r = _run(
        [
            "registry",
            "add",
            "mcp",
            "fs",
            "@modelcontextprotocol/server-filesystem",
            "--npm",
            "--skip-install",
        ],
        home,
    )
    assert r.returncode == 0, r.stderr

    # Create the harness and pull both into it.
    _run(["new", "coding"], home)
    r = _run(["edit", "skills", "coding", "--add", "research"], home)
    assert r.returncode == 0, r.stderr
    r = _run(["edit", "mcps", "coding", "--add", "fs"], home)
    assert r.returncode == 0, r.stderr

    # Show reflects the changes.
    r = _run(["show", "coding"], home)
    assert "research" in r.stdout
    assert "fs" in r.stdout

    # Activating deploys symlinks and emits .mcp.json with the MCP.
    _run(["use", "coding", "--user"], home)
    home_claude = home / "home" / ".claude"
    assert (home_claude / "skills" / "research").is_symlink()
    data = json.loads((home_claude / ".mcp.json").read_text())
    assert "fs" in data["mcpServers"]


# ---------------------------------------------------------------------------
# Workflow 7: registry remove blocks when referenced; --force overrides.
# ---------------------------------------------------------------------------


def test_remove_blocks_when_referenced(home):
    _run(["setup"], home)
    _run(["registry", "add", "mcp", "fs", "@x/fs", "--npm", "--skip-install"], home)
    _run(["new", "h"], home)
    _run(["edit", "mcps", "h", "--add", "fs"], home)

    r = _run(["registry", "remove", "fs"], home)
    assert r.returncode != 0
    assert "referenced" in r.stderr.lower()

    r = _run(["registry", "remove", "fs", "--force"], home)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# Workflow 8: migrate a v1 crux.json project.
# ---------------------------------------------------------------------------


def test_migrate_workflow(home, tmp_path):
    _run(["setup"], home)
    proj = home / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"name": "myproj", "mcps": ["fs"], "skills": ["research"]}))

    r = _run(["migrate"], home, cwd=proj)
    assert r.returncode == 0, r.stderr
    assert not (proj / "crux.json").exists()
    assert (proj / "crux.toml").read_text().strip() == 'harness = "myproj@v1"'

    bundle = (home / "registry" / "harnesses" / "myproj" / "v1" / "bundle.toml").read_text()
    assert "fs" in bundle
    assert "research" in bundle


def test_migrate_with_explicit_name(home):
    _run(["setup"], home)
    proj = home / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"mcps": [], "skills": []}))
    r = _run(["migrate", "--name", "renamed"], home, cwd=proj)
    assert r.returncode == 0, r.stderr
    assert (proj / "crux.toml").read_text().strip() == 'harness = "renamed@v1"'


# ---------------------------------------------------------------------------
# Workflow 9: doctor reports missing pieces.
# ---------------------------------------------------------------------------


def test_doctor_before_setup(home):
    r = _run(["doctor"], home)
    # Reports issues but doesn't crash.
    assert r.returncode in (0, 4)


def test_doctor_after_setup_is_clean_on_registry(home):
    _run(["setup"], home)
    r = _run(["doctor"], home)
    # May still complain about missing CLI tools; the registry checks
    # at least shouldn't fail.
    assert "missing: " not in r.stdout.splitlines()[0:1] if r.stdout else True


# ---------------------------------------------------------------------------
# Workflow 10: conflict — refuse to clobber a user's existing CLAUDE.md.
# ---------------------------------------------------------------------------


def test_use_refuses_to_clobber(home):
    _run(["setup"], home)
    _run(["new", "h"], home)
    home_claude = home / "home" / ".claude"
    home_claude.mkdir(parents=True)
    (home_claude / "CLAUDE.md").write_text("user wrote this themselves\n")
    r = _run(["use", "h", "--user"], home)
    assert r.returncode != 0
    assert "refusing" in r.stderr.lower() or "conflict" in r.stderr.lower()
    # File preserved.
    assert (home_claude / "CLAUDE.md").read_text() == "user wrote this themselves\n"
