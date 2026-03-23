# Installation

## Requirements

- **Python 3.11+**
- **macOS** or **Linux** (Windows support is planned)
- [uv](https://docs.astral.sh/uv/) — fast Python package manager (installed automatically by the installer)

## Recommended: Claude Code Plugin

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), install Crux as a plugin:

```bash
claude plugin add crux-cli/crux
```

The plugin auto-installs the `crux` CLI on your first session. It also provides the Crux skill so Claude knows all available commands.

## Alternative: Curl Installer

The fastest way to install Crux without the plugin:

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

The installer:

1. Checks for `uv` and installs it if missing
2. Installs `crux-cli` from PyPI via `uv tool install`
3. Initializes `~/.crux/` directory structure
4. Installs the bundled Crux skill for Claude Code
5. Reports any missing dependencies and next steps

## Alternative: Manual Install with uv

If you already have uv installed:

```bash
uv tool install crux-cli
crux init
```

## Alternative: pip

```bash
pip install crux-cli
crux init
```

## Verify Installation

```bash
crux version
```

Check your environment is healthy:

```bash
crux doctor
```

`crux doctor` validates your directory structure, config files, dependencies, and auto-fixes what it can.

## Upgrading

=== "Curl Installer"

    ```bash
    curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
    ```

=== "uv"

    ```bash
    uv tool upgrade crux-cli
    ```

=== "pip"

    ```bash
    pip install --upgrade crux-cli
    ```

Check for updates without installing:

```bash
crux version --check
```

## Uninstalling

```bash
uv tool uninstall crux-cli
rm -rf ~/.crux  # Remove all data
```
