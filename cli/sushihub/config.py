"""Layered configuration loading for the SushiHub CLI.

Precedence (lowest to highest):
    built-in defaults -> the package's defaults.toml -> .sushistack/workspace.toml
    -> SR_* env vars

The active platform's ``[tool.<platform>]`` table is merged over the common
``[tool]`` table, so a single file describes both Linux and Windows.

SushiStack is the umbrella workspace: the user clones it first, then `hub add`
clones the stack modules (sushiruntime, sushiengine, …) inside it. Everything the
installer downloads lands in ``<workspace>/dependencies`` and is shared by every
module, so the modules never provision their own toolchain or vcpkg tree.
"""

from __future__ import annotations

import os
import platform

from contextlib import contextmanager
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterator

# Domain-agnostic config plumbing shared by every Sushi* CLI. The generic build-
# tool schema (cmake/ninja/vcpkg paths) and the layered-load / [tool]-write
# skeleton live in sushicore; this repo adds only the SYCL-specific fields below.
from sushicore.config_base import (
    ToolConfig,
    load_tool_config,
    write_toml_document,
    write_tool_section,
)
from sushicore.workspace import (
    WORKSPACE_FILE,
    WORKSPACE_MARKER,
    has_marker,
    read_toml,
    resolve_env_path,
    walk_up,
)
from sushicore.workspace import workspace_file as _core_workspace_file

#: The checkout directory a pre-2026-09-22 workspace kept its local config in.
#: It keeps the old spelling on purpose: it names where those workspaces wrote,
#: so the rename to ``cli/`` must not follow it or the upgrade reads nothing.
CHECKOUT_CLI_DIR = Path("sushihub") / "cli"

#: The tool's own portable defaults, shipped as package data beside ``catalog.toml``.
DEFAULTS_FILE = "defaults.toml"

#: The file `hub install` wrote its ``[tool]`` paths into before 2026-09-22.
LEGACY_TOOL_FILE = "config.local.toml"

#: The file `hub link` wrote its ``[modules]`` registry into before 2026-09-22.
LEGACY_MODULES_FILE = "modules.local.toml"

#: The value written into ``[workspace] version``, as a string so it can become "1.1".
WORKSPACE_VERSION = "1"

#: The comment block every writer puts at the top of ``workspace.toml``.
WORKSPACE_HEADER = [
    "# The SushiStack workspace's own data. `hub` locates this directory by walking up from the",
    "# working directory, and everything it records about this machine lives in this one file.",
    "#",
    "# [workspace] version  the format's version, so a later `hub` can migrate this file.",
    "# [modules]            name = path, written by `hub link`.",
    "# [tool]               tool paths and the selected toolchain, written by `hub install`.",
]


def workspace_root(start: Path | None = None) -> Path:
    """Locate the SushiStack workspace root.

    The CLI is installed (pip/pipx) outside the workspace, so the package location
    tells us nothing about where the workspace lives — the invocation directory
    does. Resolution order: ``SUSHISTACK_HOME`` env var, then a walk up from CWD
    looking for the ``.sushistack`` marker. The marker is a directory since
    2026-09-22 and was a file before it; both resolve, and
    :func:`upgrade_workspace` converts the second into the first.
    """
    home = resolve_env_path("SUSHISTACK_HOME")
    if home:
        return home
    root = walk_up(start or Path.cwd(), has_marker(WORKSPACE_MARKER))
    if root is None:
        raise SystemExit(
            "Not inside a SushiStack workspace: no .sushistack marker found in the "
            "current directory or any parent. Run `hub init` first, or set "
            "SUSHISTACK_HOME to the workspace root."
        )
    return root


# Back-compat alias: diagnostics and ported code still call find_project_root.
find_project_root = workspace_root


def legacy_cli_dir(root: Path | None = None) -> Path:
    """The checkout directory a workspace kept its local config in before 2026-09-22.

    Only the `[cli]` theme is still read from here, through
    :class:`~sushicore.cli_console.LazyConsole`. Everything else the workspace owns
    lives in :func:`workspace_file` and everything the tool owns ships inside this
    package. See ``docs/design/WORKSPACE_DECOUPLING.md`` section 3.3.
    """
    root = root or workspace_root()
    return root / CHECKOUT_CLI_DIR


@contextmanager
def packaged_defaults() -> Iterator[Path]:
    """Yield a real filesystem path to the ``defaults.toml`` this package ships.

    @pre The path is valid only inside the ``with`` block, because
        ``importlib.resources`` may have extracted it.
    """
    with as_file(files("sushihub") / DEFAULTS_FILE) as path:
        yield path


def workspace_file(root: Path | None = None) -> Path:
    """The one file the workspace owns: ``<root>/.sushistack/workspace.toml``."""
    return _core_workspace_file(root or workspace_root())


def create_workspace_file(root: Path) -> Path:
    """Create *root*'s marker directory and write an empty workspace.toml into it.

    @return The path written.
    """
    (root / WORKSPACE_MARKER).mkdir(parents=True, exist_ok=True)
    return write_toml_document(
        workspace_file(root),
        {"workspace": {"version": WORKSPACE_VERSION}},
        WORKSPACE_HEADER,
    )


def upgrade_workspace(root: Path) -> bool:
    """Convert a pre-2026-09-22 workspace in place. Return whether anything changed.

    The marker used to be a file and the data used to sit in the checkout, at
    ``cli/``. This replaces the file with a directory and moves what it
    finds into ``workspace.toml``: ``modules.local.toml``'s ``[modules]`` and
    ``config.local.toml``'s ``[tool]``. The originals are left where they are, so
    the step is undone by deleting the directory.

    @pre *root* is a workspace root, old or new.
    """
    from . import console

    marker = root / WORKSPACE_MARKER
    if marker.is_dir():
        return False
    legacy = root / CHECKOUT_CLI_DIR
    tables: dict = {"workspace": {"version": WORKSPACE_VERSION}}
    modules = read_toml(legacy / LEGACY_MODULES_FILE).get("modules", {})
    if modules:
        tables["modules"] = modules
    tool = read_toml(legacy / LEGACY_TOOL_FILE).get("tool", {})
    if tool:
        tables["tool"] = tool
    if marker.exists():
        marker.unlink()
    marker.mkdir(parents=True)
    target = write_toml_document(workspace_file(root), tables, WORKSPACE_HEADER)
    console.info(f"Upgraded this workspace: its data now lives in {target}.")
    return True


# Sushi Account's base URL when neither the environment nor the config names one. The
# four endpoints under it are written down in contract/sushi-account.md.
DEFAULT_IDENTITY_URL = "https://account.sushisystems.io"


def identity_url() -> str:
    """Return the Sushi Account base URL, without its trailing slash.

    Reads ``SUSHI_ACCOUNT_URL`` first, then ``[identity] url`` from workspace.toml,
    then from the packaged defaults, then :data:`DEFAULT_IDENTITY_URL`. Outside a
    workspace the packaged defaults still answer.
    """
    override = os.environ.get("SUSHI_ACCOUNT_URL")
    if override:
        return override.rstrip("/")
    sources: list[Path] = []
    try:
        sources.append(workspace_file(workspace_root()))
    except SystemExit:
        pass
    with packaged_defaults() as defaults:
        for source in (*sources, defaults):
            url = read_toml(source).get("identity", {}).get("url")
            if isinstance(url, str) and url:
                return url.rstrip("/")
    return DEFAULT_IDENTITY_URL


def deps_dir() -> Path:
    """The single self-contained directory for everything ``hub install`` downloads.

    Everything vendorable — the intel/llvm bundle, AdaptiveCpp, a portable CMake
    and Ninja, and the vcpkg tree with its C++ library ports — lands under here,
    so a user can see exactly what was fetched and reclaim it all by deleting one
    folder (``hub remove --all``). Defaults to ``<workspace>/dependencies`` (git-
    ignored) so every module shares one tree; override with ``SUSHISTACK_DEPS_DIR``.
    Falls back to a user-local path when not inside a workspace.

    System-level prerequisites that cannot live in one folder (the host C++
    compiler — MSVC+SDK on Windows, gcc and a few -dev packages on Linux — and
    CUDA) are intentionally *not* placed here; the installer reports them instead.
    """
    override = os.environ.get("SUSHISTACK_DEPS_DIR")
    if override:
        return Path(override)
    try:
        return workspace_root() / "dependencies"
    except SystemExit:
        local = os.environ.get("LOCALAPPDATA", "")
        base = Path(local) if local else Path.home() / ".local"
        return base / "SushiStack" / "dependencies"


# The SYCL toolchains a user can select. Must match SR_SYCL_TOOLCHAIN in
# CMakeLists.txt: intel-llvm (primary), adaptivecpp (secondary), oneapi (supported).
TOOLCHAINS = ("intel-llvm", "adaptivecpp", "oneapi")

# Default compiler pair (cc, cxx) per toolchain. Used when the config does not
# pin an explicit compiler, so `sr toolchain <name>` is enough to switch.
TOOLCHAIN_COMPILERS = {
    # (cc, cxx). acpp is C++-only, so the C slot uses a plain C compiler; the
    # project builds CXX only, so cc is effectively unused but kept valid.
    "adaptivecpp": ("gcc", "acpp"),
    "intel-llvm": ("clang", "clang++"),
    "oneapi": ("icx", "icpx"),
}

# `hub install` provisions EVERYTHING by default — all three SYCL toolchains
# (intel/llvm, AdaptiveCpp, oneAPI) plus the detected GPU's toolkit. SYCL is
# a heavy ecosystem by nature, so there is no footprint-vs-breadth profile to choose: a user who is
# missing a toolchain will blame us, not their own narrowing. `hub install
# --customize` is the escape hatch — a picker for users who deliberately want a
# subset. ``active`` is written as the default SR_SYCL_TOOLCHAIN.
DEFAULT_ACTIVE_TOOLCHAIN = "intel-llvm"

# The customizable, weighty components `hub install --customize` lets a user pick.
# key -> (label, InstallContext field it gates). All default ON.
CUSTOMIZABLE_COMPONENTS = (
    ("intel-llvm",  "intel/llvm SYCL toolchain (clang++ -fsycl) — primary", "install_intel_llvm"),
    ("adaptivecpp", "AdaptiveCpp (acpp) — secondary SYCL toolchain",        "install_acpp"),
    ("oneapi",      "Intel oneAPI DPC++ (icx/icpx) — heavy, several GB",    "oneapi"),
    ("gpu",         "Toolkit for this machine's GPU, detected automatically", "gpu"),
)

# Maps a Config field to the SR_* env var that overrides it.
_ENV_OVERRIDES = {
    "toolchain": "SR_SYCL_TOOLCHAIN",
    "cc": "SR_CC",
    "cxx": "SR_CXX",
    "generator": "SR_CMAKE_GENERATOR",
    "vcpkg_root": "SR_VCPKG_ROOT",
    "oneapi_root": "SR_ONEAPI_ROOT",
    "vs_vcvars": "SR_VCVARS",
    "ninja_exe": "SR_NINJA",
    "cmake_exe": "SR_CMAKE",
    "ctest_exe": "SR_CTEST",
    "icx_compiler": "SR_ICX",
    "llvm_root": "SR_LLVM_ROOT",
    "acpp_exe": "SR_ACPP",
    "pkgconf_exe": "SR_PKGCONF",
    "doxygen_exe": "SR_DOXYGEN",
    "vcpkg_triplet": "SR_VCPKG_TRIPLET",
    "target_bin": "SR_TARGET_BIN",
}


@dataclass
class Config(ToolConfig):
    """Resolved, platform-specific tool configuration for provisioning the stack.

    Inherits the generic host build-tool fields (cmake/ninja/vcpkg paths, etc.)
    from :class:`ToolConfig` and adds the SYCL toolchain selection and compiler
    roots ``hub install`` discovers and writes into workspace.toml.
    """

    # SYCL toolchain selection (intel-llvm | adaptivecpp | oneapi). Persisted by
    # `sr toolchain` and consumed as -DSR_SYCL_TOOLCHAIN at configure time.
    toolchain: str = "intel-llvm"

    # The C compiler. Empty cc/cxx (cxx from ToolConfig) means "derive from the
    # toolchain" via TOOLCHAIN_COMPILERS.
    cc: str = ""

    oneapi_root: str = ""
    icx_compiler: str = ""
    # intel/llvm nightly bundle root (holds bin/clang++) for the intel-llvm
    # toolchain, and the AdaptiveCpp compiler for the adaptivecpp toolchain.
    # On Windows these are how the non-oneAPI toolchains provide a SYCL compiler;
    # they are discovered by `hub install` and written to workspace.toml.
    llvm_root: str = ""
    acpp_exe: str = ""

    # Run defaults
    target_bin: str = "sr_functional_tests"

    def resolved_compilers(self) -> tuple[str, str]:
        """Return (cc, cxx), deriving them from the toolchain when not pinned.

        An explicit cc/cxx in the config always wins; otherwise the pair is
        taken from TOOLCHAIN_COMPILERS so selecting a toolchain is sufficient.
        """
        default_cc, default_cxx = TOOLCHAIN_COMPILERS.get(
            self.toolchain, TOOLCHAIN_COMPILERS["intel-llvm"])
        return (self.cc or default_cc, self.cxx or default_cxx)

    def llvm_bin(self) -> str:
        """The intel/llvm bundle's bin directory, or '' when not configured."""
        root = self.expand(self.llvm_root)
        return str(Path(root) / "bin") if root else ""

    def resolved_windows_compiler(self) -> str:
        """Return the C++ compiler to drive the Windows build for the toolchain.

        Windows has no system SYCL compiler, so each toolchain points at its own:
        intel-llvm -> clang++ from the intel/llvm bundle, oneapi -> icx-cl,
        adaptivecpp -> acpp. Falls back to a bare command name when the path is
        not configured so PATH resolution still has a chance.
        """
        if self.toolchain == "oneapi":
            return self.expand(self.icx_compiler) or "icx-cl"
        if self.toolchain == "adaptivecpp":
            return self.expand(self.acpp_exe) or "acpp"
        # intel-llvm (default)
        bin_dir = self.llvm_bin()
        return str(Path(bin_dir) / "clang++.exe") if bin_dir else "clang++"


def load_config() -> Config:
    """Load and resolve the layered configuration for the current platform."""
    plat = platform.system().lower()  # 'windows' | 'linux' | 'darwin'

    root = workspace_root()
    with packaged_defaults() as defaults:
        cfg = load_tool_config(Config, [defaults, workspace_file(root)], plat, _ENV_OVERRIDES)
    # Guard against a stale/typo'd toolchain leaking through from config or env.
    if cfg.toolchain not in TOOLCHAINS:
        cfg.toolchain = "intel-llvm"
    return cfg


def set_toolchain(toolchain: str) -> Path:
    """Persist the selected SYCL toolchain into workspace.toml.

    Writes a top-level ``[tool] toolchain = "..."`` key, preserving the
    ``[tool.<platform>]`` tables `hub install` probed and every sibling table the
    file carries. Returns the path that was written.
    """
    if toolchain not in TOOLCHAINS:
        raise ValueError(f"Unknown toolchain '{toolchain}'. Choose one of {', '.join(TOOLCHAINS)}.")

    return write_tool_section(workspace_file(), {"toolchain": toolchain}, WORKSPACE_HEADER)
