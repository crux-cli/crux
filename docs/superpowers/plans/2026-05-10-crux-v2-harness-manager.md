# Crux v2.0 Harness Manager — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Crux from per-MCP/per-skill management (v1.x) to a harness-driven configuration manager (v2.0): versioned bundles of CLAUDE.md, skills, MCPs, plugins, hooks deployed via symlinks.

**Architecture:** A registry tree at `~/.crux/registry/{mcps,skills,plugins,harnesses}/` holds primitives. Harnesses are versioned bundles referencing primitives. A TOML pointer file (`~/.crux/active.toml` or `<cwd>/crux.toml`) names the active harness. `crux use` resolves the pointer, deploys symlinks under `~/.claude/` (or `<cwd>/.claude/`), and generates `.mcp.json` from the bundle's MCP references and keychain secrets.

**Tech Stack:** Python 3.11+, stdlib `tomllib` for reading TOML, a small manual writer for emitting TOML (the dialect is trivial). Reuses existing `secrets.py`, `validation.py`, `registry.py` (MCP search), `install.py`, `oauth.py`, `bridge.py`, `auth.py`, `mcp_config.py`, `preflight.py`, `health.py`.

---

## File Structure

### New modules (under `src/crux_cli/`)

- `paths.py` — extended with `registry_root()`, `mcps_root()`, `skills_root()`, `plugins_root()`, `harnesses_root()`, `active_pointer_path()`, `history_path()`, `claude_user_dir()`, `claude_dir_for()`.
- `tomlio.py` — `load_toml(path)` (stdlib `tomllib`), `dump_toml(path, data)` (manual writer; supports strings, ints, bools, lists, nested tables).
- `pointer.py` — `read_pointer(path)`, `write_pointer(path, harness_ref)`, `resolve_active(cwd)` returning `(scope, harness_name, version_or_None, pointer_path)`.
- `history.py` — `append(scope_dir, prev, new)`, `pop_previous(scope_dir)`, `read_all(scope_dir)`; bounded to 100 entries; TSV format.
- `store.py` — primitive lookups: `list_mcps()`, `list_skills()`, `list_plugins()`, `list_harnesses()`, `harness_versions(name)`, `latest_version(name)`, `harness_dir(name, version=None)`, `mcp_dir(name)`, `skill_dir(name)`, `plugin_dir(name, version)`, `load_mcp_entry(name)`, `save_mcp_entry(name, data)`.
- `bundle.py` — `load_bundle(harness_dir)`, `save_bundle(harness_dir, data)`, `Bundle` dataclass with helpers (add/remove skill/mcp/plugin).
- `harness_ops.py` — `new_harness(name)`, `bump(name)`, `show(name, version)`, `list_versions(name)`.
- `activation.py` — `activate(harness_name, version, scope, cwd)`: walks bundle, builds desired symlink set, validates no conflicts with non-Crux files, writes/replaces symlinks atomically, generates `.mcp.json` with keychain references.
- `migrate_v1.py` — `migrate_cwd(name=None)`: reads `crux.json`, creates harness, writes `crux.toml`, deletes old file.
- `setup.py` — replaces old `setup_crux.py`. Creates `~/.crux/` tree, installs bundled crux skill, writes default `config.toml`, copies shared launchers.
- `cli/main.py` — rewritten command surface per spec.
- `cli/commands/setup_cmd.py` — `crux setup`.
- `cli/commands/doctor_cmd.py` — `crux doctor`.
- `cli/commands/migrate_cmd.py` — `crux migrate`.
- `cli/commands/registry_cmd.py` — `crux registry add/remove/list`.
- `cli/commands/secret_cmd.py` — `crux secret set/list/remove`.
- `cli/commands/harness_cmd.py` — `crux new/bump/list/show/edit`.
- `cli/commands/use_cmd.py` — `crux use` and `crux active`.

### Modules removed

- `manifest.py`, `sync.py`, `projects.py`, `sandbox.py`, `setup_crux.py`.
- All of `cli/commands/{mcp,skill,project,task,version}.py` (replaced).
- All tests for the removed modules.

### Modules kept (no API change required)

- `secrets.py`, `validation.py`, `registry.py` (MCP search), `install.py` (package install helpers), `oauth.py`, `bridge.py`, `auth.py`, `mcp_config.py`, `preflight.py`, `health.py`, `config.py`, `version.py`.

### Test layout

`tests/unit/` mirrors module names with `test_<module>.py`. `tests/integration/` exercises CLI flows end-to-end with `CRUX_TEST_ROOT` redirection.

---

## Phase A — Foundation

### Task A1: Extend `paths.py` for v2 layout

**Files:**
- Modify: `src/crux_cli/paths.py`
- Test: `tests/unit/test_paths.py`

- [ ] **Step 1: Write failing test for new path helpers**

Append to `tests/unit/test_paths.py`:
```python
def test_registry_subpaths(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    from crux_cli import paths
    assert paths.registry_root() == tmp_path / "registry"
    assert paths.mcps_root() == tmp_path / "registry" / "mcps"
    assert paths.skills_root() == tmp_path / "registry" / "skills"
    assert paths.plugins_root() == tmp_path / "registry" / "plugins"
    assert paths.harnesses_root() == tmp_path / "registry" / "harnesses"
    assert paths.active_pointer_path() == tmp_path / "active.toml"
    assert paths.history_path() == tmp_path / "history"


def test_claude_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from crux_cli import paths
    assert paths.claude_user_dir() == tmp_path / ".claude"
    assert paths.claude_dir_for(tmp_path / "proj") == tmp_path / "proj" / ".claude"
```

- [ ] **Step 2: Run test** — `pytest tests/unit/test_paths.py -k "registry_subpaths or claude_dirs" -v` — expect failures.

- [ ] **Step 3: Implement helpers in `src/crux_cli/paths.py`**

Append:
```python
def registry_root() -> Path:
    return crux_home() / "registry"

def mcps_root() -> Path:
    return registry_root() / "mcps"

def skills_root() -> Path:
    return registry_root() / "skills"

def plugins_root() -> Path:
    return registry_root() / "plugins"

def harnesses_root() -> Path:
    return registry_root() / "harnesses"

def active_pointer_path() -> Path:
    return crux_home() / "active.toml"

def history_path() -> Path:
    return crux_home() / "history"

def claude_user_dir() -> Path:
    return Path.home() / ".claude"

def claude_dir_for(project_dir: Path) -> Path:
    return project_dir / ".claude"
```

- [ ] **Step 4: Verify pass** — `pytest tests/unit/test_paths.py -v`.

- [ ] **Step 5: Commit** — `git add src/crux_cli/paths.py tests/unit/test_paths.py && git commit -m "feat(paths): add v2 registry and claude-dir helpers"`.

### Task A2: `tomlio` — minimal TOML writer + reader

**Files:**
- Create: `src/crux_cli/tomlio.py`
- Create: `tests/unit/test_tomlio.py`

- [ ] **Step 1: Write failing test**

```python
import tomllib
from pathlib import Path
from crux_cli.tomlio import dump_toml, load_toml


def test_roundtrip_simple(tmp_path: Path):
    data = {"harness": "coding@v3"}
    p = tmp_path / "a.toml"
    dump_toml(p, data)
    assert load_toml(p) == data


def test_dump_tables_and_lists(tmp_path: Path):
    data = {
        "harness": {"name": "x", "version": "v2"},
        "skills": {"include": ["a", "b"]},
        "mcps": {"include": []},
    }
    p = tmp_path / "b.toml"
    dump_toml(p, data)
    assert load_toml(p) == data


def test_dump_atomic(tmp_path: Path):
    p = tmp_path / "c.toml"
    p.write_text('harness = "old"\n')
    dump_toml(p, {"harness": "new"})
    assert tomllib.loads(p.read_text())["harness"] == "new"
    # No leftover tmp files
    assert [x.name for x in tmp_path.iterdir()] == ["c.toml"]
```

- [ ] **Step 2: Run test** — expect ImportError.

- [ ] **Step 3: Implement `src/crux_cli/tomlio.py`**

```python
"""Minimal TOML I/O. Reading delegates to stdlib tomllib; writing supports the
small subset Crux emits (strings, ints, bools, flat lists, single-level tables)."""
from __future__ import annotations

import tempfile
import tomllib
from pathlib import Path
from typing import Any


def load_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _fmt_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(v, list):
        return "[" + ", ".join(_fmt_value(x) for x in v) + "]"
    raise TypeError(f"Unsupported TOML value: {type(v).__name__}")


def dump_toml(path: Path, data: dict[str, Any]) -> None:
    lines: list[str] = []
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    for k, v in scalars.items():
        lines.append(f"{k} = {_fmt_value(v)}")
    for table_name, table in tables.items():
        if lines:
            lines.append("")
        lines.append(f"[{table_name}]")
        for k, v in table.items():
            lines.append(f"{k} = {_fmt_value(v)}")
    content = "\n".join(lines) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            f.write(content)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Verify pass** — `pytest tests/unit/test_tomlio.py -v`.

- [ ] **Step 5: Commit** — `feat(tomlio): minimal TOML writer plus stdlib reader`.

### Task A3: Pointer file (read/write/resolve)

**Files:**
- Create: `src/crux_cli/pointer.py`
- Create: `tests/unit/test_pointer.py`

- [ ] **Step 1: Failing test**

```python
from pathlib import Path
import pytest
from crux_cli.pointer import read_pointer, write_pointer, parse_ref, resolve_active


def test_parse_ref():
    assert parse_ref("coding@v3") == ("coding", "v3")
    assert parse_ref("coding") == ("coding", None)


def test_parse_ref_bad():
    with pytest.raises(ValueError):
        parse_ref("@")


def test_write_then_read(tmp_path: Path):
    p = tmp_path / "crux.toml"
    write_pointer(p, "coding@v2")
    assert read_pointer(p) == ("coding", "v2")


def test_read_missing(tmp_path: Path):
    assert read_pointer(tmp_path / "absent.toml") is None


def test_resolve_walks_up(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    proj = tmp_path / "a" / "b" / "c"
    proj.mkdir(parents=True)
    write_pointer(tmp_path / "a" / "crux.toml", "x@v1")
    res = resolve_active(proj)
    assert res is not None
    scope, name, version, pointer_path = res
    assert scope == "directory"
    assert (name, version) == ("x", "v1")
    assert pointer_path == tmp_path / "a" / "crux.toml"


def test_resolve_falls_back_to_user(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    write_pointer(tmp_path / "active.toml", "global@v1")
    proj = tmp_path / "elsewhere"
    proj.mkdir()
    scope, name, version, _ = resolve_active(proj)
    assert (scope, name, version) == ("user", "global", "v1")


def test_resolve_returns_none(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    proj = tmp_path / "x"
    proj.mkdir()
    assert resolve_active(proj) is None
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement `src/crux_cli/pointer.py`**

```python
"""Pointer-file resolution: directory `crux.toml` overrides user `active.toml`."""
from __future__ import annotations

from pathlib import Path

from crux_cli.paths import active_pointer_path
from crux_cli.tomlio import dump_toml, load_toml


def parse_ref(ref: str) -> tuple[str, str | None]:
    if not ref or ref.startswith("@") or ref.endswith("@"):
        raise ValueError(f"Invalid harness ref: {ref!r}")
    if "@" in ref:
        name, version = ref.split("@", 1)
        return name, version
    return ref, None


def write_pointer(path: Path, harness_ref: str) -> None:
    parse_ref(harness_ref)  # validate
    dump_toml(path, {"harness": harness_ref})


def read_pointer(path: Path) -> tuple[str, str | None] | None:
    if not path.exists():
        return None
    data = load_toml(path)
    ref = data.get("harness")
    if not isinstance(ref, str):
        return None
    return parse_ref(ref)


def _walk_up_for_pointer(start: Path) -> Path | None:
    cur = start.resolve()
    while True:
        candidate = cur / "crux.toml"
        if candidate.exists():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent


def resolve_active(cwd: Path) -> tuple[str, str, str | None, Path] | None:
    """Return (scope, name, version, pointer_path) or None.

    scope is "directory" or "user".
    """
    found = _walk_up_for_pointer(cwd)
    if found is not None:
        parsed = read_pointer(found)
        if parsed:
            return ("directory", parsed[0], parsed[1], found)
    user_pointer = active_pointer_path()
    parsed = read_pointer(user_pointer)
    if parsed:
        return ("user", parsed[0], parsed[1], user_pointer)
    return None
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(pointer): pointer file resolution with cwd walk-up`.

### Task A4: History log

**Files:**
- Create: `src/crux_cli/history.py`
- Create: `tests/unit/test_history.py`

- [ ] **Step 1: Failing test**

```python
from pathlib import Path
from crux_cli.history import append, pop_previous, read_all


def test_append_and_pop(tmp_path: Path):
    h = tmp_path / "history"
    append(h, prev=None, new="a@v1")
    append(h, prev="a@v1", new="b@v2")
    assert pop_previous(h) == "a@v1"
    rows = read_all(h)
    assert len(rows) == 2


def test_pop_empty(tmp_path: Path):
    assert pop_previous(tmp_path / "nope") is None


def test_bounded_to_100(tmp_path: Path):
    h = tmp_path / "h"
    for i in range(120):
        append(h, prev=None, new=f"x@v{i}")
    rows = read_all(h)
    assert len(rows) == 100
    assert rows[-1][2] == "x@v119"
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""Append-only history log of harness activations (TSV, bounded to 100 rows)."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

MAX_ENTRIES = 100


def append(history_file: Path, prev: str | None, new: str) -> None:
    history_file.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\t{prev or ''}\t{new}\n"
    rows = read_all(history_file)
    rows.append((ts, prev or "", new))
    rows = rows[-MAX_ENTRIES:]
    history_file.write_text("".join(f"{r[0]}\t{r[1]}\t{r[2]}\n" for r in rows))
    _ = line  # kept for clarity; final write is authoritative


def read_all(history_file: Path) -> list[tuple[str, str, str]]:
    if not history_file.exists():
        return []
    rows: list[tuple[str, str, str]] = []
    for raw in history_file.read_text().splitlines():
        parts = raw.split("\t")
        if len(parts) >= 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def pop_previous(history_file: Path) -> str | None:
    rows = read_all(history_file)
    if not rows:
        return None
    return rows[-1][1] or None
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(history): bounded TSV history log`.

### Task A5: Bundle.toml read/write

**Files:**
- Create: `src/crux_cli/bundle.py`
- Create: `tests/unit/test_bundle.py`

- [ ] **Step 1: Failing test**

```python
from pathlib import Path
from crux_cli.bundle import load_bundle, save_bundle, default_bundle


def test_default_bundle_roundtrips(tmp_path: Path):
    save_bundle(tmp_path, default_bundle("foo", "v1"))
    b = load_bundle(tmp_path)
    assert b["harness"]["name"] == "foo"
    assert b["harness"]["version"] == "v1"
    assert b["skills"]["include"] == []
    assert b["mcps"]["include"] == []
    assert b["plugins"]["include"] == []


def test_add_remove_skill(tmp_path: Path):
    save_bundle(tmp_path, default_bundle("x", "v1"))
    b = load_bundle(tmp_path)
    b["skills"]["include"].extend(["a", "b"])
    save_bundle(tmp_path, b)
    reloaded = load_bundle(tmp_path)
    assert reloaded["skills"]["include"] == ["a", "b"]
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""bundle.toml read/write for harnesses."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from crux_cli.tomlio import dump_toml, load_toml


def default_bundle(name: str, version: str, description: str = "") -> dict[str, Any]:
    return {
        "harness": {"name": name, "version": version, "description": description},
        "skills": {"include": []},
        "mcps": {"include": []},
        "plugins": {"include": []},
        "hooks": {},
    }


def load_bundle(harness_dir: Path) -> dict[str, Any]:
    data = load_toml(harness_dir / "bundle.toml")
    data.setdefault("skills", {"include": []})
    data.setdefault("mcps", {"include": []})
    data.setdefault("plugins", {"include": []})
    data.setdefault("hooks", {})
    data["skills"].setdefault("include", [])
    data["mcps"].setdefault("include", [])
    data["plugins"].setdefault("include", [])
    return data


def save_bundle(harness_dir: Path, data: dict[str, Any]) -> None:
    harness_dir.mkdir(parents=True, exist_ok=True)
    dump_toml(harness_dir / "bundle.toml", data)
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(bundle): bundle.toml reader/writer with defaults`.

### Task A6: Store — primitive lookups

**Files:**
- Create: `src/crux_cli/store.py`
- Create: `tests/unit/test_store.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from crux_cli import store
from crux_cli.bundle import default_bundle, save_bundle


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))


def test_list_harness_versions(tmp_path):
    save_bundle(tmp_path / "registry" / "harnesses" / "foo" / "v1", default_bundle("foo", "v1"))
    save_bundle(tmp_path / "registry" / "harnesses" / "foo" / "v2", default_bundle("foo", "v2"))
    save_bundle(tmp_path / "registry" / "harnesses" / "foo" / "v10", default_bundle("foo", "v10"))
    assert store.harness_versions("foo") == ["v1", "v2", "v10"]
    assert store.latest_version("foo") == "v10"


def test_list_harnesses_empty():
    assert store.list_harnesses() == []


def test_mcp_save_load(tmp_path):
    store.save_mcp_entry("filesystem", {"type": "npm", "command": "npx", "args": ["x"]})
    assert store.load_mcp_entry("filesystem") == {"type": "npm", "command": "npx", "args": ["x"]}
    assert "filesystem" in store.list_mcps()


def test_skill_dir(tmp_path):
    (tmp_path / "registry" / "skills" / "myskill").mkdir(parents=True)
    assert "myskill" in store.list_skills()
    assert store.skill_dir("myskill").name == "myskill"


def test_plugin_versions(tmp_path):
    (tmp_path / "registry" / "plugins" / "p" / "v1").mkdir(parents=True)
    (tmp_path / "registry" / "plugins" / "p" / "v2").mkdir(parents=True)
    assert store.plugin_versions("p") == ["v1", "v2"]
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""store.py — read-only and read/write access to the registry tree."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from crux_cli import paths
from crux_cli.tomlio import dump_toml, load_toml

_VERSION_RE = re.compile(r"^v(\d+)$")


def _version_sort_key(v: str) -> tuple[int, str]:
    m = _VERSION_RE.match(v)
    return (int(m.group(1)), v) if m else (10**9, v)


def _list_subdirs(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def list_mcps() -> list[str]:
    return _list_subdirs(paths.mcps_root())


def list_skills() -> list[str]:
    return _list_subdirs(paths.skills_root())


def list_plugins() -> list[str]:
    return _list_subdirs(paths.plugins_root())


def list_harnesses() -> list[str]:
    return _list_subdirs(paths.harnesses_root())


def harness_versions(name: str) -> list[str]:
    root = paths.harnesses_root() / name
    versions = _list_subdirs(root)
    return sorted(versions, key=_version_sort_key)


def latest_version(name: str) -> str | None:
    vs = harness_versions(name)
    return vs[-1] if vs else None


def next_version(name: str) -> str:
    latest = latest_version(name)
    if not latest:
        return "v1"
    m = _VERSION_RE.match(latest)
    return f"v{int(m.group(1)) + 1}" if m else "v1"


def harness_dir(name: str, version: str | None = None) -> Path:
    if version is None:
        version = latest_version(name) or ""
    return paths.harnesses_root() / name / version


def plugin_versions(name: str) -> list[str]:
    root = paths.plugins_root() / name
    versions = _list_subdirs(root)
    return sorted(versions, key=_version_sort_key)


def plugin_dir(name: str, version: str | None = None) -> Path:
    if version is None:
        vs = plugin_versions(name)
        version = vs[-1] if vs else ""
    return paths.plugins_root() / name / version


def skill_dir(name: str) -> Path:
    return paths.skills_root() / name


def mcp_dir(name: str) -> Path:
    return paths.mcps_root() / name


def mcp_toml_path(name: str) -> Path:
    return mcp_dir(name) / "mcp.toml"


def load_mcp_entry(name: str) -> dict[str, Any]:
    return load_toml(mcp_toml_path(name))


def save_mcp_entry(name: str, data: dict[str, Any]) -> None:
    mcp_dir(name).mkdir(parents=True, exist_ok=True)
    dump_toml(mcp_toml_path(name), data)
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(store): registry tree primitive lookups`.

---

## Phase B — Activation & deployment

### Task B1: Symlink deployment planner

**Files:**
- Create: `src/crux_cli/activation.py`
- Create: `tests/unit/test_activation.py`

- [ ] **Step 1: Failing test (planning only — no fs writes)**

```python
from pathlib import Path
import pytest
from crux_cli import paths
from crux_cli.bundle import default_bundle, save_bundle
from crux_cli.activation import plan_symlinks


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def test_plan_includes_claude_md(tmp_path):
    hdir = paths.harnesses_root() / "h" / "v1"
    save_bundle(hdir, default_bundle("h", "v1"))
    (hdir / "CLAUDE.md").write_text("# h v1\n")
    plan = plan_symlinks("h", "v1", scope_target=tmp_path / "home" / ".claude")
    assert (tmp_path / "home" / ".claude" / "CLAUDE.md", hdir / "CLAUDE.md") in plan


def test_plan_includes_skills_plugins_hooks(tmp_path):
    (paths.skills_root() / "s").mkdir(parents=True)
    (paths.plugins_root() / "p" / "v2").mkdir(parents=True)
    hdir = paths.harnesses_root() / "h" / "v1"
    bundle = default_bundle("h", "v1")
    bundle["skills"]["include"] = ["s"]
    bundle["plugins"]["include"] = ["p@v2"]
    bundle["hooks"] = {"pre_tool_use": "hooks/pre.sh"}
    save_bundle(hdir, bundle)
    (hdir / "CLAUDE.md").write_text("# h\n")
    (hdir / "hooks").mkdir()
    (hdir / "hooks" / "pre.sh").write_text("#!/bin/sh\n")
    target = tmp_path / "home" / ".claude"
    plan = plan_symlinks("h", "v1", scope_target=target)
    sources = {src for _, src in plan}
    assert paths.skills_root() / "s" in sources
    assert paths.plugins_root() / "p" / "v2" in sources
    assert hdir / "hooks" / "pre.sh" in sources
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement planner in `activation.py`**

```python
"""Activation: turn a harness bundle into a symlink plan and deploy it."""
from __future__ import annotations

from pathlib import Path

from crux_cli import paths, store
from crux_cli.bundle import load_bundle


def plan_symlinks(name: str, version: str, scope_target: Path) -> list[tuple[Path, Path]]:
    """Return [(symlink_path, real_source_path), ...] for a bundle."""
    hdir = store.harness_dir(name, version)
    bundle = load_bundle(hdir)
    plan: list[tuple[Path, Path]] = []

    claude_md = hdir / "CLAUDE.md"
    if claude_md.exists():
        plan.append((scope_target / "CLAUDE.md", claude_md))

    for skill in bundle.get("skills", {}).get("include", []):
        plan.append((scope_target / "skills" / skill, store.skill_dir(skill)))

    for plugin_ref in bundle.get("plugins", {}).get("include", []):
        if "@" in plugin_ref:
            pname, pver = plugin_ref.split("@", 1)
        else:
            pname, pver = plugin_ref, None
        plan.append((scope_target / "plugins" / pname, store.plugin_dir(pname, pver)))

    hooks = bundle.get("hooks", {}) or {}
    for _key, rel in hooks.items():
        src = hdir / rel
        plan.append((scope_target / "hooks" / Path(rel).name, src))

    return plan
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(activation): plan_symlinks for harness bundle`.

### Task B2: Symlink writer with conflict detection

**Files:**
- Modify: `src/crux_cli/activation.py`
- Modify: `tests/unit/test_activation.py`

- [ ] **Step 1: Failing tests**

```python
from crux_cli.activation import apply_plan, ConflictError


def test_apply_creates_links(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    target = tmp_path / "t" / "link"
    apply_plan([(target, src)])
    assert target.is_symlink() and target.resolve() == src.resolve()


def test_apply_replaces_existing_crux_symlink(tmp_path):
    src_a = tmp_path / "a"; src_a.mkdir()
    src_b = tmp_path / "b"; src_b.mkdir()
    target = tmp_path / "t" / "link"
    apply_plan([(target, src_a)])
    apply_plan([(target, src_b)], known_registry_root=tmp_path)
    assert target.resolve() == src_b.resolve()


def test_apply_rejects_regular_file(tmp_path):
    target = tmp_path / "t" / "link"
    target.parent.mkdir(parents=True)
    target.write_text("hello")
    import pytest
    with pytest.raises(ConflictError):
        apply_plan([(target, tmp_path / "src")], known_registry_root=tmp_path)


def test_apply_rejects_foreign_symlink(tmp_path):
    foreign = tmp_path / "foreign"; foreign.mkdir()
    target = tmp_path / "t" / "link"
    target.parent.mkdir(parents=True)
    target.symlink_to(foreign)
    import pytest
    with pytest.raises(ConflictError):
        apply_plan([(target, tmp_path / "src")], known_registry_root=tmp_path / "registry")
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
class ConflictError(RuntimeError):
    """A non-Crux file/symlink blocks the target path."""


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def apply_plan(plan: list[tuple[Path, Path]], known_registry_root: Path | None = None) -> None:
    """Create the symlinks. Refuses to clobber regular files or foreign symlinks.

    `known_registry_root` defines what counts as "Crux-owned" (a symlink whose
    resolved target lives under this path may be replaced). Defaults to
    ``paths.registry_root()``.
    """
    if known_registry_root is None:
        known_registry_root = paths.registry_root()

    for target, src in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            try:
                resolved = target.resolve(strict=False)
            except OSError:
                resolved = None
            if resolved and _is_under(resolved, known_registry_root):
                target.unlink()
            else:
                raise ConflictError(f"refusing to overwrite foreign symlink: {target}")
        elif target.exists():
            raise ConflictError(f"refusing to overwrite existing file: {target}")
        target.symlink_to(src)
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(activation): apply_plan with conflict detection`.

### Task B3: `.mcp.json` generation from a bundle

**Files:**
- Create: `src/crux_cli/mcp_emit.py`
- Create: `tests/unit/test_mcp_emit.py`

- [ ] **Step 1: Failing test**

```python
import json
from pathlib import Path
import pytest
from crux_cli import store, paths
from crux_cli.bundle import default_bundle, save_bundle
from crux_cli.mcp_emit import emit_mcp_json


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))


def test_emit_npm_mcp(tmp_path):
    store.save_mcp_entry("fs", {"type": "npm", "command": "npx", "args": ["-y", "@x/fs"]})
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1")
    b["mcps"]["include"] = ["fs"]
    save_bundle(hdir, b)
    out = tmp_path / ".mcp.json"
    emit_mcp_json("h", "v1", out_path=out)
    data = json.loads(out.read_text())
    assert data["mcpServers"]["fs"]["command"] == "npx"
    assert data["mcpServers"]["fs"]["args"] == ["-y", "@x/fs"]


def test_emit_keychain_wrapped(tmp_path):
    store.save_mcp_entry("wikijs", {
        "type": "npm", "command": "npx", "args": ["-y", "wikijs-mcp"],
        "auth": {"type": "keychain", "env_vars": ["API_KEY"]},
    })
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1"); b["mcps"]["include"] = ["wikijs"]; save_bundle(hdir, b)
    out = tmp_path / ".mcp.json"
    emit_mcp_json("h", "v1", out_path=out)
    data = json.loads(out.read_text())
    e = data["mcpServers"]["wikijs"]
    assert e["env"]["CRUX_MCP_NAME"] == "wikijs"
    assert e["env"]["CRUX_AUTH_ENV_VARS"] == "API_KEY"
    assert e["command"].endswith("keychain-auth.sh")
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""Generate .mcp.json from the MCPs included in a harness bundle."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from crux_cli import paths, store
from crux_cli.bundle import load_bundle


def _build_entry(name: str, data: dict[str, Any]) -> dict[str, Any]:
    auth = data.get("auth", {}) or {}
    auth_type = auth.get("type", "")
    command = data.get("command", "")
    args = list(data.get("args", []))

    if data.get("type") == "http" or data.get("url"):
        launcher = str(paths.crux_home() / "launchers" / "http-bridge-auth.sh")
        env = {
            "CRUX_MCP_NAME": name,
            "CRUX_BRIDGE_URL": data.get("url", ""),
        }
        if auth_type == "bearer":
            env["CRUX_BRIDGE_AUTH_HEADER"] = auth.get("header_name", "Authorization")
            env["CRUX_BRIDGE_AUTH_PREFIX"] = auth.get("header_prefix", "Bearer")
            env["CRUX_BRIDGE_AUTH_ENV"] = "CRUX_AUTH_TOKEN"
            env["CRUX_AUTH_KEYCHAIN_KEY"] = auth.get("keychain_key", "API_TOKEN")
        return {"command": launcher, "args": [], "env": env}

    if auth_type == "keychain":
        launcher = str(paths.crux_home() / "launchers" / "keychain-auth.sh")
        return {
            "command": launcher,
            "args": [command, *args],
            "env": {
                "CRUX_MCP_NAME": name,
                "CRUX_AUTH_ENV_VARS": ",".join(auth.get("env_vars", [])),
            },
        }

    entry: dict[str, Any] = {"command": command, "args": args}
    if data.get("env"):
        entry["env"] = data["env"]
    return entry


def emit_mcp_json(harness_name: str, version: str, out_path: Path) -> None:
    hdir = store.harness_dir(harness_name, version)
    bundle = load_bundle(hdir)
    servers: dict[str, Any] = {}
    for name in bundle.get("mcps", {}).get("include", []):
        servers[name] = _build_entry(name, store.load_mcp_entry(name))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out_path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump({"mcpServers": servers}, f, indent=2)
        Path(tmp).replace(out_path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(mcp_emit): generate .mcp.json from harness bundle`.

### Task B4: Top-level `activate()` orchestrator

**Files:**
- Modify: `src/crux_cli/activation.py`
- Modify: `tests/unit/test_activation.py`

- [ ] **Step 1: Failing test (end-to-end on a fake home)**

```python
def test_activate_user_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    from crux_cli import paths, store
    from crux_cli.bundle import default_bundle, save_bundle
    from crux_cli.activation import activate

    # Seed registry
    store.save_mcp_entry("fs", {"type": "npm", "command": "npx", "args": ["-y", "@x/fs"]})
    (paths.skills_root() / "s").mkdir(parents=True)
    hdir = paths.harnesses_root() / "h" / "v1"
    b = default_bundle("h", "v1")
    b["skills"]["include"] = ["s"]
    b["mcps"]["include"] = ["fs"]
    save_bundle(hdir, b)
    (hdir / "CLAUDE.md").write_text("# h\n")

    activate("h", "v1", scope="user", cwd=tmp_path)

    claude_home = tmp_path / "home" / ".claude"
    assert (claude_home / "CLAUDE.md").resolve() == (hdir / "CLAUDE.md").resolve()
    assert (claude_home / "skills" / "s").resolve() == (paths.skills_root() / "s").resolve()
    import json
    data = json.loads((claude_home / ".mcp.json").read_text())
    assert "fs" in data["mcpServers"]
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement `activate()` and `deactivate()`**

```python
from crux_cli import history
from crux_cli.mcp_emit import emit_mcp_json


def _scope_target(scope: str, cwd: Path) -> Path:
    return paths.claude_user_dir() if scope == "user" else paths.claude_dir_for(cwd)


def activate(name: str, version: str, scope: str, cwd: Path) -> None:
    target = _scope_target(scope, cwd)
    target.mkdir(parents=True, exist_ok=True)
    plan = plan_symlinks(name, version, scope_target=target)
    apply_plan(plan)
    emit_mcp_json(name, version, out_path=target / ".mcp.json")
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(activation): top-level activate()`.

---

## Phase C — Harness lifecycle

### Task C1: `new` and `bump`

**Files:**
- Create: `src/crux_cli/harness_ops.py`
- Create: `tests/unit/test_harness_ops.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from crux_cli import store
from crux_cli.harness_ops import new_harness, bump


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))


def test_new_creates_v1(tmp_path):
    hdir = new_harness("foo")
    assert hdir.name == "v1"
    assert (hdir / "bundle.toml").exists()
    assert (hdir / "CLAUDE.md").exists()


def test_new_collides(tmp_path):
    new_harness("foo")
    with pytest.raises(FileExistsError):
        new_harness("foo")


def test_bump_copies_latest(tmp_path):
    hdir = new_harness("foo")
    (hdir / "CLAUDE.md").write_text("hi v1\n")
    nxt = bump("foo")
    assert nxt.name == "v2"
    assert (nxt / "CLAUDE.md").read_text() == "hi v1\n"
    assert store.harness_versions("foo") == ["v1", "v2"]


def test_bump_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        bump("nope")
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""Harness lifecycle operations: new, bump."""
from __future__ import annotations

import shutil
from pathlib import Path

from crux_cli import paths, store
from crux_cli.bundle import default_bundle, save_bundle


def new_harness(name: str, description: str = "") -> Path:
    target = paths.harnesses_root() / name
    if target.exists():
        raise FileExistsError(f"harness '{name}' already exists")
    v1 = target / "v1"
    save_bundle(v1, default_bundle(name, "v1", description))
    (v1 / "CLAUDE.md").write_text(f"# {name} v1\n\n")
    (v1 / "hooks").mkdir(exist_ok=True)
    return v1


def bump(name: str) -> Path:
    latest = store.latest_version(name)
    if latest is None:
        raise FileNotFoundError(f"harness '{name}' not found")
    nxt_version = store.next_version(name)
    src = paths.harnesses_root() / name / latest
    dst = paths.harnesses_root() / name / nxt_version
    shutil.copytree(src, dst)
    bundle_path = dst / "bundle.toml"
    from crux_cli.tomlio import dump_toml, load_toml
    data = load_toml(bundle_path)
    data.setdefault("harness", {})["version"] = nxt_version
    dump_toml(bundle_path, data)
    return dst
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(harness_ops): new and bump`.

---

## Phase D — Registry primitives

### Task D1: `registry add mcp`

**Files:**
- Create: `src/crux_cli/registry_ops.py`
- Create: `tests/unit/test_registry_ops.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from crux_cli import store
from crux_cli.registry_ops import add_mcp, add_skill_local, add_plugin_local, remove


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))


def test_add_mcp_npm(tmp_path, monkeypatch):
    monkeypatch.setattr("crux_cli.registry_ops.install_npm_package", lambda p: (True, ""))
    add_mcp("fs", source_kind="npm", source="@modelcontextprotocol/server-filesystem", skip_install=False)
    data = store.load_mcp_entry("fs")
    assert data["type"] == "npm"
    assert data["command"] == "npx"
    assert "@modelcontextprotocol/server-filesystem" in data["args"]


def test_add_mcp_with_keychain(tmp_path, monkeypatch):
    monkeypatch.setattr("crux_cli.registry_ops.install_npm_package", lambda p: (True, ""))
    add_mcp("wikijs", source_kind="npm", source="wikijs-mcp", keychain=["API_KEY"])
    data = store.load_mcp_entry("wikijs")
    assert data["auth"]["type"] == "keychain"
    assert data["auth"]["env_vars"] == ["API_KEY"]


def test_add_mcp_collision(tmp_path, monkeypatch):
    monkeypatch.setattr("crux_cli.registry_ops.install_npm_package", lambda p: (True, ""))
    add_mcp("fs", source_kind="npm", source="x")
    with pytest.raises(FileExistsError):
        add_mcp("fs", source_kind="npm", source="x")


def test_add_skill_local(tmp_path):
    src = tmp_path / "myskill"
    src.mkdir()
    (src / "SKILL.md").write_text("hello")
    add_skill_local("myskill", src)
    assert "myskill" in store.list_skills()
    assert (store.skill_dir("myskill") / "SKILL.md").exists()


def test_add_plugin_local(tmp_path):
    src = tmp_path / "p"
    src.mkdir()
    (src / "plugin.toml").write_text("hello")
    add_plugin_local("p", src, version="v1")
    assert store.plugin_versions("p") == ["v1"]


def test_remove_unreferenced(tmp_path, monkeypatch):
    monkeypatch.setattr("crux_cli.registry_ops.install_npm_package", lambda p: (True, ""))
    add_mcp("fs", source_kind="npm", source="x")
    remove("fs", force=False)
    assert "fs" not in store.list_mcps()


def test_remove_referenced_requires_force(tmp_path, monkeypatch):
    monkeypatch.setattr("crux_cli.registry_ops.install_npm_package", lambda p: (True, ""))
    add_mcp("fs", source_kind="npm", source="x")
    from crux_cli.harness_ops import new_harness
    from crux_cli.bundle import load_bundle, save_bundle
    hdir = new_harness("h")
    b = load_bundle(hdir); b["mcps"]["include"] = ["fs"]; save_bundle(hdir, b)
    with pytest.raises(RuntimeError):
        remove("fs", force=False)
    remove("fs", force=True)
    assert "fs" not in store.list_mcps()
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""registry_ops.py — add and remove registry primitives."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from crux_cli import paths, store
from crux_cli.bundle import load_bundle
from crux_cli.install import install_npm_package, install_uv_package


def _referencing_harnesses(name: str, kind: str) -> list[str]:
    refs: list[str] = []
    for harness in store.list_harnesses():
        for version in store.harness_versions(harness):
            try:
                bundle = load_bundle(store.harness_dir(harness, version))
            except Exception:
                continue
            included = bundle.get(kind, {}).get("include", []) or []
            base_names = [r.split("@", 1)[0] for r in included]
            if name in base_names:
                refs.append(f"{harness}@{version}")
    return refs


def add_mcp(
    name: str,
    *,
    source_kind: str,
    source: str,
    args: list[str] | None = None,
    keychain: list[str] | None = None,
    skip_install: bool = False,
) -> None:
    if (store.mcp_dir(name)).exists():
        raise FileExistsError(f"mcp '{name}' already exists")

    entry: dict = {"type": source_kind, "source": source}
    if source_kind == "npm":
        if not skip_install:
            ok, err = install_npm_package(source)
            if not ok:
                raise RuntimeError(err)
        entry.update({"command": "npx", "args": ["-y", source, *(args or [])]})
    elif source_kind == "uvx":
        if not skip_install:
            ok, err = install_uv_package(source)
            if not ok:
                raise RuntimeError(err)
        entry.update({"command": "uvx", "args": [source, *(args or [])]})
    elif source_kind == "github":
        dest = store.mcp_dir(name) / "source"
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", f"https://github.com/{source}", str(dest)], check=True)  # noqa: S603,S607
        entry.update({"command": "", "args": args or [], "source_dir": str(dest)})
    elif source_kind == "local":
        entry.update({"source_dir": source, "args": args or []})
    else:
        raise ValueError(f"unknown source_kind: {source_kind}")

    if keychain:
        entry["auth"] = {"type": "keychain", "env_vars": list(keychain)}

    store.save_mcp_entry(name, entry)


def add_skill_local(name: str, src: Path) -> None:
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(src)
    dst = store.skill_dir(name)
    if dst.exists():
        raise FileExistsError(f"skill '{name}' already exists")
    shutil.copytree(src, dst)


def add_skill_github(name: str, repo: str) -> None:
    dst = store.skill_dir(name)
    if dst.exists():
        raise FileExistsError(f"skill '{name}' already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", f"https://github.com/{repo}", str(dst)], check=True)  # noqa: S603,S607


def add_plugin_local(name: str, src: Path, *, version: str = "v1") -> None:
    dst = store.plugin_dir(name, version)
    if dst.exists():
        raise FileExistsError(f"plugin '{name}@{version}' already exists")
    shutil.copytree(src, dst)


def remove(name: str, *, force: bool) -> None:
    targets: list[tuple[str, Path]] = []
    if store.mcp_dir(name).exists():
        targets.append(("mcps", store.mcp_dir(name)))
    if store.skill_dir(name).exists():
        targets.append(("skills", store.skill_dir(name)))
    plugin_root = paths.plugins_root() / name
    if plugin_root.exists():
        targets.append(("plugins", plugin_root))
    if not targets:
        raise FileNotFoundError(name)
    if not force:
        for kind, _ in targets:
            refs = _referencing_harnesses(name, kind)
            if refs:
                raise RuntimeError(f"'{name}' referenced by: {', '.join(refs)} — pass force=True")
    for _kind, path in targets:
        shutil.rmtree(path)
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(registry_ops): add and remove primitives`.

---

## Phase E — Migration from v1.x

### Task E1: `migrate` command

**Files:**
- Create: `src/crux_cli/migrate_v1.py`
- Create: `tests/unit/test_migrate_v1.py`

- [ ] **Step 1: Failing test**

```python
import json
import pytest
from pathlib import Path
from crux_cli import store
from crux_cli.migrate_v1 import migrate_cwd


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path / "crux_home"))


def test_migrate_basic(tmp_path):
    proj = tmp_path / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"name": "myproj", "mcps": ["fs"], "skills": ["s"]}))
    migrate_cwd(proj)
    assert not (proj / "crux.json").exists()
    assert (proj / "crux.toml").exists()
    versions = store.harness_versions("myproj")
    assert versions == ["v1"]
    from crux_cli.bundle import load_bundle
    b = load_bundle(store.harness_dir("myproj", "v1"))
    assert b["mcps"]["include"] == ["fs"]
    assert b["skills"]["include"] == ["s"]


def test_migrate_collision(tmp_path):
    from crux_cli.harness_ops import new_harness
    new_harness("myproj")
    proj = tmp_path / "myproj"
    proj.mkdir()
    (proj / "crux.json").write_text(json.dumps({"name": "myproj", "mcps": [], "skills": []}))
    with pytest.raises(FileExistsError):
        migrate_cwd(proj)


def test_migrate_no_crux_json(tmp_path):
    with pytest.raises(FileNotFoundError):
        migrate_cwd(tmp_path)
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement**

```python
"""Migrate a v1 crux.json project to a v2 harness + pointer."""
from __future__ import annotations

import json
from pathlib import Path

from crux_cli.bundle import load_bundle, save_bundle
from crux_cli.harness_ops import new_harness
from crux_cli.pointer import write_pointer


def migrate_cwd(project_dir: Path, *, name: str | None = None) -> str:
    crux_json = project_dir / "crux.json"
    if not crux_json.exists():
        raise FileNotFoundError(crux_json)
    data = json.loads(crux_json.read_text())

    harness_name = name or data.get("name") or project_dir.name
    hdir = new_harness(harness_name)
    bundle = load_bundle(hdir)
    bundle["mcps"]["include"] = list(data.get("mcps", []))
    bundle["skills"]["include"] = list(data.get("skills", []))
    save_bundle(hdir, bundle)

    write_pointer(project_dir / "crux.toml", f"{harness_name}@v1")
    crux_json.unlink()
    return harness_name
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(migrate): v1 crux.json → v2 harness + pointer`.

---

## Phase F — Setup

### Task F1: Setup module

**Files:**
- Modify: `src/crux_cli/setup_crux.py` → trim to v2 logic (or replace with new `setup.py`)
- Create: `src/crux_cli/setup.py`
- Create: `tests/unit/test_setup_v2.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from crux_cli import paths
from crux_cli.setup import run_setup


@pytest.fixture(autouse=True)
def _redir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))


def test_run_setup_creates_tree(tmp_path):
    res = run_setup()
    for d in [paths.crux_home(), paths.registry_root(), paths.mcps_root(),
              paths.skills_root(), paths.plugins_root(), paths.harnesses_root(),
              paths.crux_home() / "launchers"]:
        assert d.exists()
    assert res.dirs_created
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement `src/crux_cli/setup.py`**

```python
"""v2 setup: create registry tree, install bundled crux skill, install launchers."""
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


def run_setup() -> SetupResult:
    res = SetupResult()

    for d in [
        paths.crux_home(),
        paths.registry_root(),
        paths.mcps_root(),
        paths.skills_root(),
        paths.plugins_root(),
        paths.harnesses_root(),
        paths.crux_home() / "launchers",
    ]:
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
```

- [ ] **Step 4: Verify pass**.

- [ ] **Step 5: Commit** — `feat(setup): v2 setup creates registry tree and installs skill`.

---

## Phase G — CLI surface

### Task G1: New `cli/main.py` with v2 command surface

**Files:**
- Replace: `src/crux_cli/cli/main.py`
- Create: `src/crux_cli/cli/commands/setup_cmd.py`
- Create: `src/crux_cli/cli/commands/doctor_cmd.py`
- Create: `src/crux_cli/cli/commands/migrate_cmd.py`
- Create: `src/crux_cli/cli/commands/registry_cmd.py`
- Create: `src/crux_cli/cli/commands/secret_cmd.py`
- Create: `src/crux_cli/cli/commands/harness_cmd.py`
- Create: `src/crux_cli/cli/commands/use_cmd.py`
- Create: `tests/integration/test_cli_v2.py`

- [ ] **Step 1: Failing integration test**

```python
import json
import os
import subprocess
import sys
import pytest


def _run(args, env_root, cwd=None):
    env = os.environ.copy()
    env["CRUX_TEST_ROOT"] = str(env_root)
    env["HOME"] = str(env_root / "home")
    (env_root / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, "-m", "crux_cli", *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


def test_setup_and_new(tmp_path):
    r = _run(["setup"], tmp_path)
    assert r.returncode == 0, r.stderr
    r = _run(["new", "coding"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "registry" / "harnesses" / "coding" / "v1" / "bundle.toml").exists()


def test_use_user_scope(tmp_path):
    _run(["setup"], tmp_path)
    _run(["new", "coding"], tmp_path)
    r = _run(["use", "coding", "--user"], tmp_path)
    assert r.returncode == 0, r.stderr
    home_claude = tmp_path / "home" / ".claude"
    assert (home_claude / "CLAUDE.md").is_symlink()
    # active pointer set
    pointer = (tmp_path / "active.toml").read_text()
    assert "coding" in pointer


def test_active_command(tmp_path):
    _run(["setup"], tmp_path)
    _run(["new", "coding"], tmp_path)
    _run(["use", "coding", "--user"], tmp_path)
    r = _run(["active"], tmp_path, cwd=tmp_path)
    assert r.returncode == 0
    assert "coding" in r.stdout
```

- [ ] **Step 2: Run** — failure expected.

- [ ] **Step 3: Implement `crux_cli/__init__.py` module entry**

```python
# src/crux_cli/__main__.py
from crux_cli.cli.main import main
if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implement `cli/main.py`**

```python
"""crux v2 CLI entry point."""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    from crux_cli.cli.commands.doctor_cmd import cmd_doctor
    from crux_cli.cli.commands.harness_cmd import (
        cmd_bump, cmd_edit, cmd_list, cmd_new, cmd_show,
    )
    from crux_cli.cli.commands.migrate_cmd import cmd_migrate
    from crux_cli.cli.commands.registry_cmd import (
        cmd_registry_add, cmd_registry_list, cmd_registry_remove,
    )
    from crux_cli.cli.commands.secret_cmd import (
        cmd_secret_list, cmd_secret_remove, cmd_secret_set,
    )
    from crux_cli.cli.commands.setup_cmd import cmd_setup
    from crux_cli.cli.commands.use_cmd import cmd_active, cmd_use

    p = argparse.ArgumentParser(prog="crux", description="Crux — Harness manager for Claude Code")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("setup").set_defaults(func=cmd_setup)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    m = sub.add_parser("migrate")
    m.add_argument("--name", help="Override harness name")
    m.set_defaults(func=cmd_migrate)

    # registry
    rp = sub.add_parser("registry")
    rs = rp.add_subparsers(dest="reg_cmd", required=True)
    ra = rs.add_parser("add")
    ra.add_argument("kind", choices=["mcp", "skill", "plugin"])
    ra.add_argument("name")
    ra.add_argument("source")
    ra.add_argument("--npm", dest="npm", action="store_true")
    ra.add_argument("--uvx", dest="uvx", action="store_true")
    ra.add_argument("--github", dest="github", action="store_true")
    ra.add_argument("--local", dest="local", action="store_true")
    ra.add_argument("--keychain", help="Comma-separated env vars for keychain auth")
    ra.add_argument("--args", help="Extra args, space-separated")
    ra.add_argument("--skip-install", action="store_true")
    ra.add_argument("--version", default="v1", help="Plugin version (default v1)")
    ra.set_defaults(func=cmd_registry_add)
    rr = rs.add_parser("remove")
    rr.add_argument("name")
    rr.add_argument("--force", action="store_true")
    rr.set_defaults(func=cmd_registry_remove)
    rl = rs.add_parser("list")
    rl.set_defaults(func=cmd_registry_list)

    # secret
    sp = sub.add_parser("secret")
    ss = sp.add_subparsers(dest="secret_cmd", required=True)
    sset = ss.add_parser("set")
    sset.add_argument("mcp"); sset.add_argument("key")
    sset.add_argument("--value", help="Value (otherwise prompted)")
    sset.set_defaults(func=cmd_secret_set)
    sl = ss.add_parser("list"); sl.add_argument("mcp", nargs="?")
    sl.set_defaults(func=cmd_secret_list)
    srm = ss.add_parser("remove"); srm.add_argument("mcp"); srm.add_argument("key")
    srm.set_defaults(func=cmd_secret_remove)

    # harness lifecycle
    n = sub.add_parser("new"); n.add_argument("name"); n.set_defaults(func=cmd_new)
    b = sub.add_parser("bump"); b.add_argument("name"); b.set_defaults(func=cmd_bump)
    li = sub.add_parser("list"); li.add_argument("name", nargs="?"); li.set_defaults(func=cmd_list)
    sh = sub.add_parser("show"); sh.add_argument("ref"); sh.set_defaults(func=cmd_show)

    # edit
    ep = sub.add_parser("edit")
    es = ep.add_subparsers(dest="edit_what", required=True)
    for what in ("claude", "skills", "mcps", "plugins", "hooks"):
        sub_e = es.add_parser(what)
        sub_e.add_argument("ref", nargs="?")
        sub_e.add_argument("--add", action="append", default=[])
        sub_e.add_argument("--remove", action="append", default=[])
        sub_e.set_defaults(func=cmd_edit, edit_what=what)

    # activation
    u = sub.add_parser("use")
    u.add_argument("ref", help="Harness ref (use '-' for previous, '--none' to deactivate)", nargs="?")
    u.add_argument("--user", action="store_true")
    u.add_argument("--none", dest="none", action="store_true")
    u.set_defaults(func=cmd_use)
    sub.add_parser("active").set_defaults(func=cmd_active)

    args = p.parse_args()
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"crux: not found: {e}", file=sys.stderr)
        sys.exit(2)
    except FileExistsError as e:
        print(f"crux: exists: {e}", file=sys.stderr)
        sys.exit(3)
    except RuntimeError as e:
        print(f"crux: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Implement each command file (setup_cmd, doctor_cmd, migrate_cmd, registry_cmd, secret_cmd, harness_cmd, use_cmd).**

Each command is a thin wrapper over the core modules. See command stubs:

```python
# src/crux_cli/cli/commands/setup_cmd.py
from __future__ import annotations
import argparse
from crux_cli.setup import run_setup


def cmd_setup(args: argparse.Namespace) -> None:
    res = run_setup()
    print(f"setup: created {len(res.dirs_created)} dirs, "
          f"skill={'ok' if res.skill_installed else 'skip'}, "
          f"launchers={len(res.launchers_installed)}")
```

```python
# src/crux_cli/cli/commands/use_cmd.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from crux_cli import history, paths, store
from crux_cli.activation import activate
from crux_cli.pointer import parse_ref, read_pointer, resolve_active, write_pointer


def _pointer_path_for(scope: str, cwd: Path) -> Path:
    return paths.active_pointer_path() if scope == "user" else cwd / "crux.toml"


def _history_for(scope: str, cwd: Path) -> Path:
    return paths.history_path() if scope == "user" else cwd / ".crux" / "history"


def cmd_use(args: argparse.Namespace) -> None:
    cwd = Path.cwd()
    scope = "user" if args.user else "directory"
    pointer = _pointer_path_for(scope, cwd)

    if args.none:
        if pointer.exists():
            pointer.unlink()
        print(f"use: deactivated ({scope})")
        return

    if args.ref == "-":
        prev = history.pop_previous(_history_for(scope, cwd))
        if not prev:
            print("crux: use: no previous harness in history", file=sys.stderr)
            sys.exit(3)
        ref = prev
    else:
        ref = args.ref

    if not ref:
        print("crux: use: missing harness reference", file=sys.stderr)
        sys.exit(1)

    name, version = parse_ref(ref)
    if version is None:
        version = store.latest_version(name)
        if not version:
            raise FileNotFoundError(f"harness '{name}'")

    prev_parsed = read_pointer(pointer)
    prev_ref = f"{prev_parsed[0]}@{prev_parsed[1] or store.latest_version(prev_parsed[0]) or 'v?'}" if prev_parsed else ""

    activate(name, version, scope=scope, cwd=cwd)
    write_pointer(pointer, f"{name}@{version}")
    history.append(_history_for(scope, cwd), prev=prev_ref or None, new=f"{name}@{version}")
    print(f"use: {name}@{version} ({scope})")


def cmd_active(args: argparse.Namespace) -> None:
    res = resolve_active(Path.cwd())
    if res is None:
        print("active: (none)")
        return
    scope, name, version, pointer_path = res
    print(f"active: {name}@{version or 'latest'} ({scope}, {pointer_path})")
```

```python
# src/crux_cli/cli/commands/harness_cmd.py
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

from crux_cli import store
from crux_cli.bundle import load_bundle, save_bundle
from crux_cli.harness_ops import bump, new_harness
from crux_cli.pointer import parse_ref


def cmd_new(args):
    hdir = new_harness(args.name)
    print(f"new: created {args.name}@v1 at {hdir}")


def cmd_bump(args):
    hdir = bump(args.name)
    print(f"bump: created {args.name}@{hdir.name}")


def cmd_list(args):
    name = getattr(args, "name", None)
    if name:
        for v in store.harness_versions(name):
            print(v)
    else:
        for h in store.list_harnesses():
            versions = store.harness_versions(h)
            print(f"{h}: {', '.join(versions)}")


def _resolve_ref(ref):
    name, version = parse_ref(ref)
    if version is None:
        version = store.latest_version(name)
        if version is None:
            raise FileNotFoundError(f"harness '{name}'")
    return name, version


def cmd_show(args):
    name, version = _resolve_ref(args.ref)
    hdir = store.harness_dir(name, version)
    bundle = load_bundle(hdir)
    print(f"# {name}@{version}")
    print(f"description: {bundle.get('harness', {}).get('description', '')}")
    print(f"skills:  {', '.join(bundle['skills']['include'])}")
    print(f"mcps:    {', '.join(bundle['mcps']['include'])}")
    print(f"plugins: {', '.join(bundle['plugins']['include'])}")
    hooks = bundle.get("hooks", {}) or {}
    if hooks:
        print("hooks:")
        for k, v in hooks.items():
            print(f"  {k} = {v}")


def cmd_edit(args):
    ref = args.ref
    if ref is None:
        from crux_cli.pointer import resolve_active
        res = resolve_active(Path.cwd())
        if res is None:
            print("crux: edit: no active harness", file=sys.stderr)
            sys.exit(2)
        _scope, name, version, _ = res
        if version is None:
            version = store.latest_version(name)
    else:
        name, version = _resolve_ref(ref)

    hdir = store.harness_dir(name, version)
    bundle = load_bundle(hdir)

    what = args.edit_what
    if what == "claude":
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, str(hdir / "CLAUDE.md")], check=False)  # noqa: S603
        return
    if what == "hooks":
        (hdir / "hooks").mkdir(exist_ok=True)
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, str(hdir / "hooks")], check=False)  # noqa: S603
        return

    key = {"skills": "skills", "mcps": "mcps", "plugins": "plugins"}[what]
    include = bundle[key]["include"]
    for item in (args.add or []):
        if item not in include:
            include.append(item)
    for item in (args.remove or []):
        if item in include:
            include.remove(item)
    bundle[key]["include"] = include
    save_bundle(hdir, bundle)
    print(f"edit {what}: {', '.join(include)}")
```

```python
# src/crux_cli/cli/commands/registry_cmd.py
from __future__ import annotations
import argparse
from pathlib import Path

from crux_cli import paths, store
from crux_cli.registry_ops import (
    add_mcp, add_plugin_local, add_skill_github, add_skill_local, remove,
)


def cmd_registry_add(args):
    extra_args = args.args.split() if getattr(args, "args", None) else []
    keychain = [v.strip() for v in args.keychain.split(",")] if getattr(args, "keychain", None) else None
    if args.kind == "mcp":
        if args.npm:
            kind = "npm"
        elif args.uvx:
            kind = "uvx"
        elif args.github:
            kind = "github"
        elif args.local:
            kind = "local"
        else:
            kind = "npm"
        add_mcp(args.name, source_kind=kind, source=args.source, args=extra_args,
                keychain=keychain, skip_install=args.skip_install)
        print(f"registry: added mcp {args.name}")
    elif args.kind == "skill":
        if args.github:
            add_skill_github(args.name, args.source)
        else:
            add_skill_local(args.name, Path(args.source))
        print(f"registry: added skill {args.name}")
    elif args.kind == "plugin":
        add_plugin_local(args.name, Path(args.source), version=args.version)
        print(f"registry: added plugin {args.name}@{args.version}")


def cmd_registry_remove(args):
    remove(args.name, force=args.force)
    print(f"registry: removed {args.name}")


def cmd_registry_list(args):
    print("# mcps:")
    for n in store.list_mcps(): print(f"  {n}")
    print("# skills:")
    for n in store.list_skills(): print(f"  {n}")
    print("# plugins:")
    for n in store.list_plugins():
        for v in store.plugin_versions(n):
            print(f"  {n}@{v}")
```

```python
# src/crux_cli/cli/commands/secret_cmd.py
from __future__ import annotations
import argparse
import getpass
import sys

from crux_cli.secrets import load_secrets_index, save_secrets_index


def _backend():
    from crux_cli.secrets import get_backend
    return get_backend()


def cmd_secret_set(args):
    val = args.value or getpass.getpass(f"value for {args.mcp}/{args.key}: ")
    _backend().set(args.mcp, args.key, val)
    idx = load_secrets_index()
    idx.setdefault(args.mcp, [])
    if args.key not in idx[args.mcp]:
        idx[args.mcp].append(args.key)
    save_secrets_index(idx)
    print(f"secret: set {args.mcp}/{args.key}")


def cmd_secret_list(args):
    idx = load_secrets_index()
    for mcp, keys in idx.items():
        if args.mcp and mcp != args.mcp:
            continue
        print(f"{mcp}: {', '.join(keys)}")


def cmd_secret_remove(args):
    _backend().remove(args.mcp, args.key)
    idx = load_secrets_index()
    if args.mcp in idx:
        idx[args.mcp] = [k for k in idx[args.mcp] if k != args.key]
        if not idx[args.mcp]:
            del idx[args.mcp]
        save_secrets_index(idx)
    print(f"secret: removed {args.mcp}/{args.key}")
```

```python
# src/crux_cli/cli/commands/migrate_cmd.py
from __future__ import annotations
import argparse
from pathlib import Path

from crux_cli.migrate_v1 import migrate_cwd


def cmd_migrate(args):
    name = migrate_cwd(Path.cwd(), name=getattr(args, "name", None))
    print(f"migrate: created harness {name}@v1 and crux.toml pointer")
```

```python
# src/crux_cli/cli/commands/doctor_cmd.py
from __future__ import annotations
import argparse
import shutil
import sys

from crux_cli import paths


def cmd_doctor(args):
    issues = 0
    for d in [paths.crux_home(), paths.registry_root(), paths.mcps_root(),
              paths.skills_root(), paths.plugins_root(), paths.harnesses_root()]:
        if not d.exists():
            print(f"missing: {d} — run `crux setup`")
            issues += 1
    for tool in ("git", "uv", "npm", "claude"):
        if shutil.which(tool) is None:
            print(f"missing tool: {tool}")
            issues += 1
    if issues:
        sys.exit(4)
    print("doctor: ok")
```

- [ ] **Step 6: Helper — secrets `get_backend()`**

The existing `secrets.py` already exposes a backend selector — confirm `get_backend()` exists and exports cleanly. If not, add a thin shim. (See implementation phase — adapt as needed.)

- [ ] **Step 7: Verify pass** — `pytest tests/integration/test_cli_v2.py -v`.

- [ ] **Step 8: Commit** — `feat(cli): v2 command surface (setup/registry/secret/new/bump/list/show/edit/use/active/migrate/doctor)`.

---

## Phase H — Remove v1 code

### Task H1: Delete obsolete modules and tests

**Files removed:**
- `src/crux_cli/manifest.py`
- `src/crux_cli/sync.py`
- `src/crux_cli/projects.py`
- `src/crux_cli/sandbox.py`
- `src/crux_cli/setup_crux.py`
- `src/crux_cli/cli/commands/{mcp,skill,project,task,version}.py`
- All tests with v1 module names (manifest, sync, projects, sandbox*, setup, mcp_install, mcp_remove_secrets, init, oauth/bridge/auth/preflight may be retained as they're still used).

- [ ] **Step 1: Delete files**

```bash
git rm src/crux_cli/manifest.py src/crux_cli/sync.py src/crux_cli/projects.py \
       src/crux_cli/sandbox.py src/crux_cli/setup_crux.py \
       src/crux_cli/cli/commands/mcp.py src/crux_cli/cli/commands/skill.py \
       src/crux_cli/cli/commands/project.py src/crux_cli/cli/commands/task.py \
       src/crux_cli/cli/commands/version.py src/crux_cli/cli/commands/doctor.py
git rm tests/unit/test_manifest.py tests/unit/test_sync.py tests/unit/test_projects.py \
       tests/unit/test_sandbox.py tests/unit/test_sandbox_extended.py \
       tests/unit/test_mcp_install.py tests/unit/test_mcp_remove_secrets.py \
       tests/unit/test_setup.py tests/unit/test_init.py
git rm tests/integration/test_cli_mcp.py tests/integration/test_cli_skill.py \
       tests/integration/test_cli_project_create.py tests/integration/test_cli_project_sync.py \
       tests/integration/test_cli_doctor.py tests/integration/test_cli_task.py \
       tests/integration/test_e2e_auth.py || true
git rm conftest.py tests/conftest.py tests/fixtures -r || true
```

- [ ] **Step 2: Re-add a minimal root `conftest.py` and `tests/conftest.py`**

```python
# conftest.py
from __future__ import annotations
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def pytest_configure(config):
    src = str(REPO_ROOT / "src")
    parts = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    if src not in parts:
        parts.insert(0, src)
    os.environ["PYTHONPATH"] = os.pathsep.join(parts)
```

- [ ] **Step 3: Bump version**

Edit `pyproject.toml` `version = "2.0.0"` and `src/crux_cli/version.py` accordingly.

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/ -v
```

Expect: all green.

- [ ] **Step 5: Commit** — `chore(v2): remove v1 modules and stale tests; bump to 2.0.0`.

---

## Phase I — Docs & polish

### Task I1: Update README and CLI docs

**Files:**
- Modify: `README.md`
- Modify: `docs/...` (any references to v1 commands)

- [ ] **Step 1: Update README's quickstart and command reference to match v2 surface**

- [ ] **Step 2: Commit** — `docs: v2 README and CLI reference`.

---

## Self-Review Checklist

- Every command from the spec section "Command surface" has a CLI parser + handler:
  - `setup`, `doctor`, `migrate`, `registry add/remove/list`, `secret set/list/remove`,
  - `new`, `bump`, `list`, `show`,
  - `edit claude/skills/mcps/plugins/hooks`,
  - `use [-] [--none] [--user]`, `active`.
- Pointer file resolution implements cwd-walk → user fallback.
- `crux use -` reads history and re-runs activation.
- `.mcp.json` is generated (not symlinked) and includes keychain env-var refs.
- Symlink writer refuses to clobber regular files / foreign symlinks.
- Migration is cwd-only, creates harness named after `crux.json`'s name (or `--name`), deletes `crux.json`.
- All paths obey `CRUX_TEST_ROOT` for test isolation.
- Exit codes mapped (1 usage, 2 not-found, 3 state, 4 environment).
