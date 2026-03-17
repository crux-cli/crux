"""Crux CLI - Personal control plane for AI agent tooling."""

try:
    from importlib.metadata import version

    __version__ = version("crux-cli")
except Exception:
    __version__ = "0.0.1"
