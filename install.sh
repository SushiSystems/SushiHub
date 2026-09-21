#!/usr/bin/env bash
# SushiStack one-script installer (Linux / WSL).
#
# Bootstraps Python, pip and Git, installs the `hub` CLI from PyPI with pipx,
# then runs `hub init` and `hub install` in the directory you choose. Nothing is
# cloned: a workspace is any directory `hub init` has marked. The portable
# CMake/Ninja lands in <workspace>/dependencies, so only Python and Git need
# bootstrapping here.
#
# Git is still installed because `hub add` clones module checkouts with it, not
# because the workspace itself comes from a clone.
#
# An install made this way carries no desktop application; `hub gui` needs the
# SushiStack repository, which you clone yourself if you want it.
#
# `hub install` provisions what the present modules declare, which in a fresh
# workspace is the base build tools alone. Each module added below brings its own
# toolchains as it arrives; `hub install --customize` picks a different set.
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
# Usage (from a local copy):
#   bash install.sh [--add "..."] [--dry-run] [--no-alias]
#
# SUSHISTACK_DIR names the workspace directory and skips the prompt.
#
# The installer offers, once, to append `alias sh='hub'` to the interactive shell
# rc file. `--no-alias` declines without asking.
set -euo pipefail

DRY_FLAG=""
MODULES=""
NO_ALIAS=0
expect_add=0
for arg in "$@"; do
  if [ "$expect_add" -eq 1 ]; then MODULES="$arg"; expect_add=0; continue; fi
  case "$arg" in
    --add)         expect_add=1 ;;
    --add=*)       MODULES="${arg#*=}" ;;
    --dry-run)     DRY_FLAG="--dry-run" ;;
    --no-alias)    NO_ALIAS=1 ;;
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

ALIAS_MARKER="# sushi hub alias"

# Name the rc file the user's login shell reads when it starts interactively.
alias_rc_file() {
  case "${SHELL:-}" in
    */zsh) printf '%s\n' "$HOME/.zshrc" ;;
    *)     printf '%s\n' "$HOME/.bashrc" ;;
  esac
}

# Ask once whether to append `alias sh='hub'`, and append it if the answer is yes.
offer_alias() {
  [ "$NO_ALIAS" -eq 1 ] && return 0
  [ -t 0 ] || return 0
  rc_file="$(alias_rc_file)"
  if [ -f "$rc_file" ] && grep -qF "$ALIAS_MARKER" "$rc_file"; then return 0; fi

  log "The alias only changes what you type in an interactive shell; /bin/sh and every #!/bin/sh script keep the real sh."
  printf '\033[1;34m[INFO]\033[0m Add `alias sh='"'"'hub'"'"'` to %s? [y/N] ' "$rc_file"
  if ! IFS= read -r reply; then printf '\n'; return 0; fi
  case "$reply" in
    [yY]|[yY][eE][sS]) ;;
    *) return 0 ;;
  esac

  printf '\n%s\nalias sh=%s\n' "$ALIAS_MARKER" "'hub'" >> "$rc_file"
  log "Alias written to $rc_file; open a new shell or run: . $rc_file"
}

# Only Python and Git need bootstrapping; everything else is downloaded by `hub
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

# Choose the workspace directory. It need not exist and need not be a checkout;
# `hub init` marks whatever directory it is run in.
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
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"
log "Workspace: $WORKSPACE_DIR"

# Install the hub CLI from PyPI. pipx is bootstrapped here rather than reused
# from the repository's install.py, because that file arrives with a checkout and
# this script no longer makes one.
if ! command -v pipx >/dev/null 2>&1; then
  log "pipx not found; installing it with pip..."
  python3 -m pip install --user pipx || python3 -m pip install --user --break-system-packages pipx
  python3 -m pipx ensurepath
fi

# Name a command that runs pipx: its own shim when PATH carries one, otherwise
# the module under python3. `ensurepath` only edits the rc file, so the shim may
# not be on PATH until the next shell.
if command -v pipx >/dev/null 2>&1; then PIPX="pipx"; else PIPX="python3 -m pipx"; fi

# Remove any existing sushihub venv first. `pipx install --force` reuses the venv
# it finds, which fails when that venv was built another way -- an editable
# install from a checkout is the common case, and it is exactly what a
# contributor upgrading to the published package has.
if $PIPX list --short 2>/dev/null | grep -q '^sushihub'; then
  log "Replacing the existing sushihub install"
  $PIPX uninstall sushihub
fi

log "Installing the hub CLI from PyPI..."
$PIPX install sushihub || err "Could not install sushihub from PyPI."

PIPX_BIN_DIR=$($PIPX environment --value PIPX_BIN_DIR)

# An install made before 2026-09-22 published the same CLI under another
# distribution name, whose venv keeps its own `hub` shim.
if $PIPX list --short 2>/dev/null | grep -q '^sushistack-cli'; then
  log "Removing the sushistack-cli install this package was renamed from"
  $PIPX uninstall sushistack-cli
fi

# An install from before the rename left a shim named ss, which shadows iproute2's.
if [ -e "$PIPX_BIN_DIR/ss" ]; then
  log "Removing the ss shim an earlier install left in $PIPX_BIN_DIR"
  rm -f "$PIPX_BIN_DIR/ss"
fi

HUB_CMD="$PIPX_BIN_DIR/hub"
if [ ! -x "$HUB_CMD" ]; then HUB_CMD="hub"; fi

# Mark the workspace, then provision what it declares today: the base tools.
"$HUB_CMD" init
log "Running: hub install $DRY_FLAG"
"$HUB_CMD" install $DRY_FLAG
HUB_EXIT=$?
if [ "$HUB_EXIT" -ne 0 ]; then exit "$HUB_EXIT"; fi

# Optionally clone the requested modules; `hub add` provisions what each needs.
if [ -n "$MODULES" ]; then
  log "Adding modules: $MODULES"
  # shellcheck disable=SC2086
  "$HUB_CMD" add $MODULES
fi

offer_alias

log "Done. Workspace ready at $WORKSPACE_DIR"
if [ -z "$MODULES" ]; then
  log "Next: hub add sushiruntime   (then: cd sushiruntime && sr build)"
fi
