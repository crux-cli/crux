"""v2 setup.

Creates the ``~/.crux/`` tree (registry subdirs and launchers dir),
writes a default ``config.toml`` if absent, installs the bundled crux
skill into the registry, and copies shared launcher scripts.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from crux_cli import paths
from crux_cli.config import default_config, save_config

_BUNDLED_SKILL = Path(__file__).resolve().parent / "data" / "skills" / "crux" / "SKILL.md"
_BUNDLED_LAUNCHERS = Path(__file__).resolve().parent / "data" / "launchers"


@dataclass
class SetupResult:
    dirs_created: list[str] = field(default_factory=list)
    config_written: bool = False
    skill_installed: bool = False
    launchers_installed: list[str] = field(default_factory=list)


def _required_dirs() -> list[Path]:
    return [
        paths.crux_home(),
        paths.registry_root(),
        paths.mcps_root(),
        paths.skills_root(),
        paths.plugins_root(),
        paths.harnesses_root(),
        paths.crux_home() / "launchers",
    ]


def run_setup() -> SetupResult:
    """Idempotent: re-running is safe and only fills in what's missing."""
    res = SetupResult()

    for d in _required_dirs():
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            res.dirs_created.append(str(d))

    cfg_path = paths.crux_home() / "config.toml"
    if not cfg_path.exists():
        save_config(default_config(), path=cfg_path)
        res.config_written = True

    skill_dst = paths.skills_root() / "crux"
    skill_dst.mkdir(parents=True, exist_ok=True)
    if _BUNDLED_SKILL.exists():
        shutil.copy2(_BUNDLED_SKILL, skill_dst / "SKILL.md")
        res.skill_installed = True

    if _BUNDLED_LAUNCHERS.is_dir():
        target = paths.crux_home() / "launchers"
        for script in _BUNDLED_LAUNCHERS.glob("*.sh"):
            dst = target / script.name
            shutil.copy2(script, dst)
            dst.chmod(0o755)
            res.launchers_installed.append(script.name)

    return res
