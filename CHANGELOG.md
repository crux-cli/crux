# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
