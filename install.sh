#!/usr/bin/env bash
# SushiStack one-script installer (Linux / WSL).
#
# Bootstraps Python, pip, and Git, clones the SushiStack workspace, installs the
# `ss` CLI, then provisions the shared dependency tree with `ss install`. The
# portable CMake/Ninja lands in <workspace>/dependencies, so only Python and Git
# need bootstrapping here.
#
# `ss install` provisions what the present modules declare, which in a fresh
# workspace is the base build tools alone. Each module added below brings its own
# toolchains as it arrives; `ss install --customize` picks a different set.
#
# Supports Debian/Ubuntu (apt), Fedora/RHEL (dnf/yum), Arch (pacman), and
# openSUSE (zypper).
#
# Module checkouts (cloned into the workspace, each with the toolchains it needs):
#   --add "sushiruntime sushiengine"  space- or comma-separated list (default: none)
#
# Usage (bare machine):
#   curl -fsSL https://sushisystems.io/install.sh | bash -s -- --add "sushiruntime sushiengine"
#
# Usage (inside a checkout):
#   bash install.sh [--add "..."] [--dry-run]
set -euo pipefail

REPO_URL="${SUSHISTACK_REPO_URL:-https://github.com/sushisystems/sushistack.git}"
DRY_FLAG=""
MODULES=""
expect_add=0
for arg in "$@"; do
  if [ "$expect_add" -eq 1 ]; then MODULES="$arg"; expect_add=0; continue; fi
  case "$arg" in
    --add)         expect_add=1 ;;
    --add=*)       MODULES="${arg#*=}" ;;
    --dry-run)     DRY_FLAG="--dry-run" ;;
    *) printf '[WARN] unknown argument: %s\n' "$arg" ;;
  esac
done
# Normalise commas to spaces so `--add a,b` and `--add "a b"` both work.
MODULES="${MODULES//,/ }"

log() { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

bootstrap_apt()    { log "Installing Python and Git via apt...";    $SUDO apt-get update -qq && $SUDO apt-get install -y python3 python3-pip git; }
bootstrap_dnf()    { log "Installing Python and Git via dnf...";    $SUDO dnf install -y python3 python3-pip git; }
bootstrap_yum()    { log "Installing Python and Git via yum...";    $SUDO yum install -y python3 python3-pip git; }
bootstrap_pacman() { log "Installing Python and Git via pacman..."; $SUDO pacman -Sy --noconfirm python python-pip git; }
bootstrap_zypper() { log "Installing Python and Git via zypper..."; $SUDO zypper install -y python3 python3-pip git; }

# Only Python and Git need bootstrapping; everything else is downloaded by `ss
# install` into the shared dependencies/ tree.
need_bootstrap=0
for tool in python3 git; do
  command -v "$tool" >/dev/null 2>&1 || need_bootstrap=1
done
python3 -m pip --version >/dev/null 2>&1 || need_bootstrap=1

if [ "$need_bootstrap" -eq 1 ]; then
  if   command -v apt-get  >/dev/null 2>&1; then bootstrap_apt
  elif command -v dnf      >/dev/null 2>&1; then bootstrap_dnf
  elif command -v yum      >/dev/null 2>&1; then bootstrap_yum
  elif command -v pacman   >/dev/null 2>&1; then bootstrap_pacman
  elif command -v zypper   >/dev/null 2>&1; then bootstrap_zypper
  else
    err "No supported package manager found (apt, dnf, yum, pacman, zypper). Install python3, pip, and git manually, then re-run."
  fi
fi

# Locate or clone the workspace. The SushiStack repo is identified by its
# cli/manifests tree (it ships no CMakeLists.txt).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/cli/manifests" ]; then
  WORKSPACE_DIR="$SCRIPT_DIR"
else
  DEFAULT_WORKSPACE_DIR="$HOME/sushistack"
  if [ -n "${SUSHISTACK_DIR:-}" ]; then
    WORKSPACE_DIR="$SUSHISTACK_DIR"
  elif [ -t 0 ] && [ -t 1 ]; then
    printf '\033[1;34m[INFO]\033[0m Install location [%s] (30s to answer, Enter to accept): ' "$DEFAULT_WORKSPACE_DIR"
    if IFS= read -r -t 30 REPLY_DIR; then
      WORKSPACE_DIR="${REPLY_DIR:-$DEFAULT_WORKSPACE_DIR}"
    else
      printf '\n'
      log "No input received, using default: $DEFAULT_WORKSPACE_DIR"
      WORKSPACE_DIR="$DEFAULT_WORKSPACE_DIR"
    fi
  else
    WORKSPACE_DIR="$DEFAULT_WORKSPACE_DIR"
  fi
  if [ ! -d "$WORKSPACE_DIR/.git" ]; then
    log "Cloning $REPO_URL -> $WORKSPACE_DIR"
    git clone "$REPO_URL" "$WORKSPACE_DIR"
  fi
fi
cd "$WORKSPACE_DIR"
log "Workspace: $WORKSPACE_DIR"

# Install the ss CLI.
log "Installing the ss CLI..."
python3 cli/install.py

PIPX_BIN_DIR=$(python3 -m pipx environment --value PIPX_BIN_DIR)
SS_CMD="$PIPX_BIN_DIR/ss"
if [ ! -x "$SS_CMD" ]; then SS_CMD="ss"; fi

# Mark the workspace, then provision what it declares today: the base tools.
"$SS_CMD" init
log "Running: ss install $DRY_FLAG"
"$SS_CMD" install $DRY_FLAG
SS_EXIT=$?
if [ "$SS_EXIT" -ne 0 ]; then exit "$SS_EXIT"; fi

# Optionally clone the requested modules; `ss add` provisions what each needs.
if [ -n "$MODULES" ]; then
  log "Adding modules: $MODULES"
  # shellcheck disable=SC2086
  "$SS_CMD" add $MODULES
fi

log "Done. Workspace ready at $WORKSPACE_DIR"
if [ -z "$MODULES" ]; then
  log "Next: ss add sushiruntime   (then: cd sushiruntime && sr build)"
fi
