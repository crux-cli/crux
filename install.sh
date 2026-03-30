#!/usr/bin/env sh
# Crux installer
# Usage: curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
set -e

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BOLD='\033[1m'
DIM='\033[2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

step()    { printf "\n${BOLD}  %s${RESET}\n\n" "$*"; }
info()    { printf "  ${CYAN}→${RESET}  %s\n" "$*"; }
success() { printf "  ${GREEN}✓${RESET}  %s\n" "$*"; }
warn()    { printf "  ${YELLOW}!${RESET}  %s\n" "$*"; }
fatal()   { printf "\n  ${RED}✗  Error:${RESET} %s\n\n" "$*" >&2; exit 1; }
dim()     { printf "     ${DIM}%s${RESET}\n" "$*"; }

CRUX_BIN_DIR="${HOME}/.local/bin"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
printf "\n"
printf "  ${BOLD}╔════════════════════════════════════╗${RESET}\n"
printf "  ${BOLD}║                                    ║${RESET}\n"
printf "  ${BOLD}║   crux  ·  AI agent control plane  ║${RESET}\n"
printf "  ${BOLD}║                                    ║${RESET}\n"
printf "  ${BOLD}╚════════════════════════════════════╝${RESET}\n"

# ---------------------------------------------------------------------------
# OS check
# ---------------------------------------------------------------------------
OS="$(uname -s)"
case "${OS}" in
  Darwin) OS_NAME="macOS" ;;
  Linux)  OS_NAME="Linux" ;;
  *)      fatal "Unsupported OS: ${OS}. Crux supports macOS and Linux." ;;
esac

ARCH="$(uname -m)"
info "Platform: ${OS_NAME} (${ARCH})"

# ---------------------------------------------------------------------------
# Step 1 — uv
# ---------------------------------------------------------------------------
step "Step 1/3  uv package manager"

if command -v uv >/dev/null 2>&1; then
  UV_VER="$(uv --version 2>&1 | awk '{print $2}')"
  success "uv ${UV_VER} already installed"
else
  info "uv not found — fetching official installer..."

  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    fatal "curl or wget is required to install uv. Please install one and retry."
  fi

  # Pick up uv in the current shell session
  UV_ENV="${HOME}/.local/bin/env"
  if [ -f "${UV_ENV}" ]; then
    # shellcheck disable=SC1090
    . "${UV_ENV}"
  else
    export PATH="${CRUX_BIN_DIR}:${PATH}"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    fatal "uv was installed but is not on PATH. Add ${CRUX_BIN_DIR} to your PATH and re-run."
  fi

  UV_VER="$(uv --version 2>&1 | awk '{print $2}')"
  success "uv ${UV_VER} installed"
fi

# ---------------------------------------------------------------------------
# Step 2 — crux-cli
# ---------------------------------------------------------------------------
step "Step 2/3  crux-cli"

if command -v crux >/dev/null 2>&1; then
  CRUX_VER="$(crux version 2>&1 | head -1)"
  warn "crux is already installed (${CRUX_VER})"
  info "To upgrade run:  uv tool upgrade crux-cli"
else
  info "Installing crux-cli from PyPI..."
  uv tool install crux-cli
  success "crux-cli installed to ${CRUX_BIN_DIR}/crux"
fi

# Initialise ~/.crux/ (idempotent)
info "Initialising ~/.crux/ home directory..."
"${CRUX_BIN_DIR}/crux" init >/dev/null 2>&1 && success "~/.crux/ ready" || true

# ---------------------------------------------------------------------------
# Step 3 — PATH & skill
# ---------------------------------------------------------------------------
step "Step 3/3  Shell setup"

# ---- PATH check ------------------------------------------------------------
PATH_CONFIGURED=false
case ":${PATH}:" in
  *":${CRUX_BIN_DIR}:"*) PATH_CONFIGURED=true ;;
esac

if "${PATH_CONFIGURED}"; then
  success "${CRUX_BIN_DIR} is already in PATH"
else
  # Detect the right rc file for the user's shell
  SHELL_NAME="$(basename "${SHELL:-sh}")"
  case "${SHELL_NAME}" in
    zsh)  RC_FILE="${ZDOTDIR:-${HOME}}/.zshrc" ;;
    bash) RC_FILE="${HOME}/.bashrc" ;;
    fish) RC_FILE="${HOME}/.config/fish/config.fish" ;;
    *)    RC_FILE="${HOME}/.profile" ;;
  esac

  warn "${CRUX_BIN_DIR} is not in your PATH"
  printf "\n  Add crux to your PATH:\n\n"

  if [ "${SHELL_NAME}" = "fish" ]; then
    printf "  ${CYAN}fish_add_path %s${RESET}\n" "${CRUX_BIN_DIR}"
  else
    printf "  ${CYAN}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> %s${RESET}\n" "${RC_FILE}"
    printf "  ${CYAN}source %s${RESET}\n" "${RC_FILE}"
  fi
  printf "\n"
fi

# ---- Skill install prompt --------------------------------------------------
SKILL_DEST="${HOME}/.claude/skills/crux/SKILL.md"
if [ -f "${SKILL_DEST}" ]; then
  success "Crux skill already installed for Claude Code"
else
  printf "  Install the Crux skill so Claude Code knows how to use it:\n\n"
  printf "  ${CYAN}crux init${RESET}\n"
  dim "Installs SKILL.md → ~/.claude/skills/crux/"
  printf "\n"
fi

# ---------------------------------------------------------------------------
# Done — next steps
# ---------------------------------------------------------------------------
printf "\n  ${GREEN}${BOLD}✓  Crux is ready!${RESET}\n"
printf "\n  ${BOLD}Quick start:${RESET}\n\n"
printf "  ${CYAN}crux doctor${RESET}\n"
dim "verify environment and dependencies"
printf "\n"
printf "  ${CYAN}crux mcp search <query>${RESET}\n"
dim "browse the MCP registry"
printf "\n"
printf "  ${CYAN}crux mcp add <name> --npm <package>${RESET}\n"
dim "install and register an MCP server"
printf "\n"
printf "  ${CYAN}crux mcp auth <name>${RESET}\n"
dim "authenticate an MCP server"
printf "\n"
printf "  ${CYAN}crux project create${RESET}\n"
dim "create a project with crux.json"
printf "\n"
printf "  ${DIM}docs  →  https://github.com/crux-cli/crux${RESET}\n\n"
