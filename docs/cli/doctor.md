# crux doctor

Diagnose and auto-fix Crux environment issues.

## Usage

```bash
crux doctor
```

## Description

Runs a comprehensive set of environment checks and auto-fixes what it can. Checks include:

- Python version (3.11+ required)
- External tools on PATH (`git`, `node`/`npx`, `uv`)
- `~/.crux/` directory structure
- Registry JSON integrity
- MCP source directories
- Build artifacts for compiled MCPs
- `crux` binary on PATH

## Output

Each check shows a pass/fail/warning status:

```
✓ Python 3.12.0 (>= 3.11 required)
✓ git found
✓ node found
✓ npx found
✗ MCP 'wikijs' source not found at ~/.crux/mcps/wikijs
  Fix: crux mcp add wikijs --github jaalbin24/wikijs-mcp-server
```

## Examples

```bash
crux doctor
```
