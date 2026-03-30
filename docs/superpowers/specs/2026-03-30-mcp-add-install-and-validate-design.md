# Design: Install and validate MCP servers during `crux mcp add`

## Problem

`crux mcp add` registers MCP servers in `registry.json` without installing dependencies or verifying the server works. All failures are deferred to agent runtime, where they're harder to debug and disrupt active tasks.

Three open issues describe this:
- **#27**: `--npm`/`--uv` packages are never downloaded or validated
- **#28**: `--github` repos are cloned but dependencies aren't installed
- **#29**: No runtime health check (addressed by probe step)

## Design

Each MCP type follows: **install -> register -> probe -> rollback on failure**.

### `--npm <pkg>`

1. Run `npm install -g <pkg>` to permanently install the package globally. This downloads, links the binary, and makes it available to npx immediately.
2. If install fails (E404, network error, missing entrypoint, incompatible platform) -> report error, don't register.
3. Write entry to `registry.json`.
4. Probe via `probe_mcp_server_detailed` (JSON-RPC handshake, 60s timeout).
5. If probe returns `"failed"` -> delete registry entry, run `npm uninstall -g <pkg>`, report error.

### `--uv <pkg>`

1. Run `uv tool install <pkg>` to permanently install the tool into `~/.local/share/uv/tools/`. This creates a persistent venv, installs deps, and links the entrypoint. Subsequent `uvx <pkg>` invocations use the installed version instantly.
2. If install fails (yanked, no versions, build error, incompatible Python) -> report error, don't register.
3. Write entry to `registry.json`.
4. Probe via `probe_mcp_server_detailed` (60s timeout).
5. If probe returns `"failed"` -> delete registry entry, run `uv tool uninstall <pkg>`, report error.

### `--github <user/repo>`

1. Clone repo (existing behavior).
2. Auto-detect project type and install dependencies:
   - `package.json` found -> `npm install` always, then `npm run build` if build script exists (fixes current `detect_and_run_build` which skips `npm install` when no build script).
   - `pyproject.toml` found -> `uv sync`.
   - `requirements.txt` found (no pyproject.toml) -> `uv venv && uv pip install -r requirements.txt`.
   - None found -> skip (may be a pre-built binary or script).
3. If install fails -> delete cloned directory, report error, don't register.
4. Write entry to `registry.json`.
5. If `--command` is specified -> probe. If probe fails -> delete cloned dir, delete registry entry, report error.
6. If no `--command` -> skip probe (can't run what we don't know how to start).

### `--local <path>`

1. Copy source (existing behavior).
2. Same dependency detection and install as `--github`.
3. If install fails -> delete copied dir, report error, don't register.
4. Write entry to `registry.json`.
5. If `--command` specified -> probe. If probe fails -> rollback.

## Implementation details

### Probe timeout

`probe_mcp_server_detailed` currently hardcodes a 10-second timeout. Add an optional `timeout` parameter (default 10). `crux mcp add` passes `timeout=60` to allow for first-run downloads.

### Dependency installation function

Replace `detect_and_run_build` with `detect_and_install_deps(dest, entry)` that handles:
- npm projects: always `npm install`, then conditionally `npm run build`
- Python projects: `uv sync` or `uv pip install -r requirements.txt`
- Returns `(ok, error_message)` tuple

### Rollback

A helper function `rollback_mcp_add(name, entry, reg)` that:
- Removes the entry from registry if it was added
- Deletes `source_dir` if it's under `~/.crux/`
- For uvx: runs `uv tool uninstall <pkg>`

### `--skip-validation` flag

Skips both the installation verification step AND the probe. Use cases:
- MCPs that require auth before starting (probe would fail on auth check)
- Offline registration
- Private registries

### Delete `package_validation.py`

The separate `npm cache add` / `uv pip install --dry-run` approach is replaced entirely by direct installation + probe. The module is removed.

## Files to modify

- `src/crux_cli/cli/commands/mcp.py` — `cmd_mcp_add`, replace `detect_and_run_build` with `detect_and_install_deps`, add probe + rollback
- `src/crux_cli/health.py` — add `timeout` parameter to `probe_mcp_server_detailed`
- `src/crux_cli/package_validation.py` — delete
- `tests/unit/test_package_validation.py` — delete, replace with tests for new install + probe flow
- `tests/unit/test_health.py` — update for timeout parameter
- `tests/integration/test_cli_mcp.py` — update tests

## Out of scope

- `crux mcp test <name>` as a standalone command (issue #29 asks for this but it's a separate feature)
- Auth-aware probing (servers that need credentials to start will fail the probe — use `--skip-validation`)
