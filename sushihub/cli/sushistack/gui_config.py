"""What the desktop application is, said once for the shared build machinery.

`ss gui` builds `sushihub/gui` the way a module CLI builds its own repository:
through :class:`sushicore.cmake_driver.CMakeDriver` under a snapshotted
environment, against the vcpkg tree `ss install` provisions. That machinery asks
for a profile and a config, and this module is where the application answers.

The application is not a module checkout. It lives inside the workspace `ss`
already owns, so its root is a fixed path under the workspace root and its
configuration is the workspace's own — there is no second config directory to
find.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from pathlib import Path

from sushicore.config_base import load_tool_config
from sushicore.profile import ModuleProfile
from sushicore.stack_config import StackConfig

from .config import config_dir, deps_dir, workspace_root

#: How the desktop application describes itself to the shared build machinery.
#: Read by the environment snapshot's cache key and by the run target, so the
#: two cannot disagree about what is being built.
GUI_PROFILE = ModuleProfile(
    name="SushiHub GUI",
    program="ss gui",
    env_prefix="SS_GUI",
    root_marker="CMakeLists.txt",
    default_target="sushihub_gui",
)

#: The application's directory, relative to the workspace root.
GUI_DIR = Path("sushihub") / "gui"


def gui_root(workspace: Path | None = None) -> Path:
    """Locate the desktop application's source directory.

    Args:
        workspace: The workspace root, or None to resolve it from the
            environment and the current directory.

    Returns:
        The directory holding the application's CMakeLists.txt.

    Raises:
        SystemExit: When that directory carries no CMakeLists.txt, which is what
            a workspace checked out without the application looks like.
    """
    root = (workspace or workspace_root()) / GUI_DIR
    if not (root / GUI_PROFILE.root_marker).is_file():
        raise SystemExit(
            f"No {GUI_PROFILE.name} sources at {root}: the workspace carries no "
            f"{GUI_PROFILE.root_marker} there. Update the workspace checkout "
            "(`ss update`) and try again.")
    return root


@dataclass
class GuiConfig(StackConfig):
    """Tool configuration for the desktop application's build.

    Inherits the host tool paths from :class:`sushicore.config_base.ToolConfig`
    and the shared-tree vcpkg resolution from
    :class:`sushicore.stack_config.StackConfig`.
    """


    def resolved_compiler(self, root: Path) -> str:
        """Return the configured C++ compiler, or '' to let CMake choose one.

        :class:`StackConfig` prefers the bundled SYCL clang++, which is right for
        the modules that compile SYCL and wrong here: the application is plain
        C++17 and builds with the MSVC that vcvars puts on PATH, or with the
        system compiler on Linux. Empty means the configure passes no
        CMAKE_CXX_COMPILER at all and CMake searches the snapshotted
        environment. See docs/agent/plans/2026-09-05-wave-4b-gui-through-ss.md.

        Args:
            root: The application's source directory.

        Returns:
            The expanded ``cxx`` when one is configured, else the empty string.
        """
        return self.expand(self.cxx) if self.cxx else ""

    def standalone_deps_dir(self, root: Path) -> Path:
        """Return the dependency tree to use when no workspace marker is found.

        The application ships inside the workspace, so this is reached only when
        the marker is gone; ``ss``'s own fallback is then the single answer both
        halves of the CLI give.

        Args:
            root: The application's source directory.
        """
        return deps_dir()


def load_gui_config() -> GuiConfig:
    """Load the layered configuration the application builds under.

    Precedence, low to high: the workspace's config.toml, its config.local.toml
    (what `ss install` writes), then the ``SS_GUI_*`` environment overrides.
    """
    cfg_dir = config_dir()
    return load_tool_config(
        GuiConfig,
        [cfg_dir / "config.toml", cfg_dir / "config.local.toml"],
        platform.system().lower(),
        GUI_PROFILE.env_overrides(),
    )
