# Changelog

All notable changes to Crux are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **`crux mcp add --npm`** now runs `npm install -g` to install packages globally before registering. Catches missing packages, build failures, and platform incompatibilities at registration time instead of agent runtime.
- **`crux mcp add --uv`** now runs `uv tool install` to permanently install Python tools before registering. Catches yanked versions, missing packages, and build errors immediately.
- **`crux mcp add --github`** now auto-detects project type and installs dependencies after cloning: `package.json` triggers `npm install` (+ `npm run build` if build script exists), `pyproject.toml` triggers `uv sync`, `requirements.txt` triggers `uv venv && uv pip install -r requirements.txt`.
- **`crux mcp add --local`** now runs the same dependency auto-detection and installation as `--github`.
- Renamed CLI flags: `--npx` is now `--npm`, `--uvx` is now `--uv`.

### Added

- **`--skip-validation` flag** for `crux mcp add`: bypasses installation and dependency checks. Useful for MCPs that require auth before installation, offline registration, or private registries.

## [1.0.0] - 2026-03-16

### Added

- **Registry management**: `crux add mcp/skill`, `crux remove`, `crux list`, `crux search`, `crux upgrade`
- **Project manifests**: `crux init`, `crux install`, `crux uninstall` with per-project `crux.json`
- **Config generation**: `crux sync` generates `.mcp.json` and platform-aware launcher scripts
- **Secrets management**: `crux secret set/get/delete/list` with 3 backends (macOS Keychain, Linux Secret Service, age-encrypted file)
- **Sandbox execution**: `crux run` with 6-check pre-flight validation, timeout support, process group cleanup
- **Health & diagnostics**: `crux status` with rich tables, `crux doctor` with 12 environment checks
- **Project tracking**: `~/.crux/projects.json` with stale path detection
- **Version checking**: `crux version --check` queries PyPI with semantic version comparison
- **Setup & migration**: `crux setup` creates `~/.crux/` structure, migrates from old marketplace layout
- **Bundled skill**: Claude Code skill installed to `~/.claude/skills/crux/` during setup
- **Input validation**: MCP/skill name validation, registry/crux.json schema validation
- **Security hardening**: path traversal prevention, shell injection prevention, atomic file writes, process group cleanup on timeout

### Security

- Secrets never stored in files — only in OS keystore
- Launcher scripts contain keystore lookup commands, not embedded values
- All file paths validated before `shutil.rmtree` operations
- MCP names and env var names validated before shell script embedding
- Sandbox `run_id` validated to prevent path traversal
- Process groups killed on timeout (prevents orphaned MCP servers)
- `~/.claude` backed up (not deleted) during doctor fixes
