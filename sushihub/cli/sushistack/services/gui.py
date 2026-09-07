"""Build, test, run and clean policy for the desktop application.

What cache variables the application's configure passes, where its build tree
lives and which executable `run` launches are decisions this module owns; how a
cmake command line is spawned is :class:`sushicore.cmake_driver.CMakeDriver`'s.
The split is the one every module CLI in the stack keeps, so the application is
built the way sushiblas is rather than by a second mechanism.

The build tree is ``build/hub`` under the application, beside the ``build/<preset>``
trees CMakePresets.json writes. The two never share a directory: a preset build
runs under whatever environment the shell already had, and this one runs under the
vcvars snapshot, so a cache written by one is wrong for the other.

The configure turns vcpkg's manifest mode off. `hub install` fills a classic-mode
tree under ``dependencies/vcpkg`` and manifest mode ignores it, which is what the
failed configure in docs/agent/plans/2026-09-05-wave-4b-gui-through-ss.md showed.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from pathlib import Path

from sushicore.cmake_driver import CMakeDriver
from sushicore.discovery import ExecutableIndex
from sushicore.proc import Runner

from .. import console
from ..gui_config import GUI_PROFILE, GuiConfig, gui_root, load_gui_config
from ..gui_env import load_gui_build_env


class BuildType(str, enum.Enum):
    """The configurations the application can be built in."""

    debug = "debug"
    release = "release"
    relwithdebinfo = "relwithdebinfo"


#: Each build type as CMAKE_BUILD_TYPE spells it.
_CMAKE_BUILD_TYPE = {
    BuildType.debug: "Debug",
    BuildType.release: "Release",
    BuildType.relwithdebinfo: "RelWithDebInfo",
}

#: What a command says when the build tree it needs is not there yet.
_NOT_BUILT = "build/hub not found. Run `hub gui build` first."

_RUNNER = Runner(console, GUI_PROFILE.program)
_DRIVER = CMakeDriver(console, _RUNNER)

# The vendored dependencies cmake fetches are not programs the user asked for.
_EXECUTABLES = ExecutableIndex(skip_dirs=("_deps",))


def _build_dir(root: Path) -> Path:
    """Return the build tree `hub gui` owns under the application root."""
    return root / "build" / "hub"


def _configure_args(cfg: GuiConfig, root: Path, build_dir: Path, build_type: str,
                    defines: Sequence[str] | None = None) -> list[str]:
    """Assemble the configure command line for the application.

    Args:
        cfg: The resolved configuration.
        root: The application's source directory.
        build_dir: The tree to configure into.
        build_type: CMAKE_BUILD_TYPE's value.
        defines: Caller-supplied ``VAR=VALUE`` cache entries.

    Returns:
        The full argv, with the caller's defines last so an explicit one is
        never outranked by a default this function sets.

    Raises:
        ValueError: When a define carries no ``=``.
    """
    args = [
        _DRIVER.cmake(cfg), "-S", str(root), "-B", str(build_dir), "-G", cfg.generator,
        f"-DCMAKE_BUILD_TYPE={build_type}",
    ]

    if compiler := cfg.resolved_compiler(root):
        args.append(f"-DCMAKE_CXX_COMPILER={compiler}")
    if cfg.ninja_exe:
        args.append(f"-DCMAKE_MAKE_PROGRAM={cfg.expand(cfg.ninja_exe)}")

    if vcpkg := cfg.resolved_vcpkg(root):
        args += [
            f"-DCMAKE_TOOLCHAIN_FILE={vcpkg}/scripts/buildsystems/vcpkg.cmake",
            f"-DVCPKG_ROOT={vcpkg}",
        ]
        if cfg.is_windows:
            args.append(f"-DVCPKG_TARGET_TRIPLET={cfg.vcpkg_triplet}")

    args += ["-DVCPKG_MANIFEST_MODE=OFF", "-DSUSHIHUB_GUI_BUILD_TESTS=ON"]

    for entry in defines or ():
        if "=" not in entry:
            raise ValueError(
                f"-D expects VAR=VALUE, got {entry!r}. Use VAR= to clear a variable.")
        args.append(f"-D{entry}")

    return args


def build(build_type: BuildType = BuildType.debug, clean: bool = False,
          defines: Sequence[str] | None = None, *, driver=None, env_loader=None) -> int:
    """Configure and compile the desktop application.

    Args:
        build_type: The configuration to build.
        clean: Remove the build tree before configuring.
        defines: Extra ``VAR=VALUE`` cache entries for the configure.
        driver: The cmake driver, or None for the shared one.
        env_loader: The build-environment loader, or None for the vcvars snapshot.

    Returns:
        The exit code: 0 on success, 2 on a malformed define.
    """
    driver = driver or _DRIVER
    env_loader = env_loader or load_gui_build_env

    console.header("Desktop Application Build")
    root = gui_root()
    cfg = load_gui_config()
    cmake_build_type = _CMAKE_BUILD_TYPE[build_type]
    build_dir = _build_dir(root)

    try:
        configure_args = _configure_args(cfg, root, build_dir, cmake_build_type, defines)
    except ValueError as exc:
        console.error(str(exc))
        return 2

    if clean:
        driver.clean_tree(build_dir)

    fresh = driver.needs_configure(build_dir, cfg.generator, root=root,
                                   expect={"CMAKE_BUILD_TYPE": cmake_build_type})
    if fresh:
        console.info(f"Configuring CMake... (type={build_type.value})")
        if build_dir.is_dir():
            driver.clean_tree(build_dir)
    else:
        console.info("Reconfiguring in place...")

    env = env_loader(cfg, build_dir)
    rc = driver.configure(configure_args, cwd=root, env=env)
    if rc != 0:
        console.error("CMake configure failed.")
        return rc

    console.info("Building...")
    rc = driver.compile(cfg, build_dir, cwd=root, env=env, config=cmake_build_type)
    if rc == 0:
        console.success("Build completed successfully!")
    else:
        console.error("Build failed.")
    return rc


def test(filter: str | None = None, repeat: int = 0, *, driver=None,
         env_loader=None) -> int:
    """Run the application's CTest suites.

    The application labels no test, so every registered case runs and *filter*
    selects among them by name.

    Args:
        filter: A ctest ``-R`` pattern over the "Suite.Case" names.
        repeat: Re-run each selected test until it fails or this many runs pass.
        driver: The cmake driver, or None for the shared one.
        env_loader: The build-environment loader, or None for the vcvars snapshot.

    Returns:
        The exit code; 1 when the application has not been built yet.
    """
    driver = driver or _DRIVER
    env_loader = env_loader or load_gui_build_env

    console.header("Desktop Application Test")
    root = gui_root()
    cfg = load_gui_config()
    build_dir = _build_dir(root)
    if not build_dir.is_dir():
        console.error(_NOT_BUILT)
        return 1

    env = env_loader(cfg, build_dir)
    return driver.ctest_run(cfg, build_dir, env, filter=filter, repeat=repeat)


def run(target: str | None = None, args: Sequence[str] = (), *, runner=None,
        env_loader=None) -> int:
    """Launch a program the application's build tree holds.

    Args:
        target: The executable to launch, or None for the application itself.
        args: Arguments handed to that executable.
        runner: The process runner, or None for the shared one.
        env_loader: The build-environment loader, or None for the vcvars snapshot.

    Returns:
        The child's exit code; 1 when the tree is missing or holds no such program.
    """
    runner = runner or _RUNNER
    env_loader = env_loader or load_gui_build_env

    console.header("Desktop Application Run")
    root = gui_root()
    cfg = load_gui_config()
    build_dir = _build_dir(root)
    if not build_dir.is_dir():
        console.error(_NOT_BUILT)
        return 1

    env = env_loader(cfg, build_dir)
    exe = _EXECUTABLES.resolve(build_dir, console, target=target, default=GUI_PROFILE.default_target)
    if exe is None:
        return 1

    console.info(f"Executing: {exe.name}")
    return runner.run([str(exe), *args], root, env)


def clean(*, driver=None) -> int:
    """Remove the build tree `hub gui` owns.

    Args:
        driver: The cmake driver, or None for the shared one.
    """
    driver = driver or _DRIVER
    console.header("Desktop Application Clean")
    driver.clean_tree(_build_dir(gui_root()))
    return 0
