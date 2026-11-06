# ports.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Declares the five ports a `hub` command reaches the outside through, and their bundle.

The console, git, pipx, the Sushi Account client and the release host. Each machine adapter sits
beside the code it wraps; the in-memory ones are in :mod:`sushihub.services.memory`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence

from .identity import Account, DeviceCode, LicenceToken, ReleaseInfo


class RichPrinter(Protocol):
    """The Rich console behind a :class:`ConsolePort`, for lines that carry markup."""

    def print(self, *objects: object, **options: object) -> None:
        """Prints *objects* with Rich markup."""
        ...


class ConsolePort(Protocol):
    """The console calls a command prints through."""

    @property
    def console(self) -> RichPrinter:
        """Returns the Rich console behind this one."""
        ...

    def prompt(self, message: str, default: str | None = None) -> str:
        """Asks *message* and returns the answer, or *default* when the answer is empty."""
        ...

    def header(self, title: str) -> None:
        """Prints a section header."""
        ...

    def info(self, text: str) -> None:
        """Prints an information line."""
        ...

    def success(self, text: str) -> None:
        """Prints a success line."""
        ...

    def warn(self, text: str) -> None:
        """Prints a warning line."""
        ...

    def error(self, text: str) -> None:
        """Prints an error line."""
        ...

    def table(self, columns: Sequence[str], rows: Sequence[Sequence[str]], title: str = "") -> None:
        """Prints a table."""
        ...

    def progress(self, label: str, index: int, count: int, fraction: float | None = None) -> None:
        """Prints one progress step."""
        ...


class GitClient(Protocol):
    """Runs git for a module checkout."""

    def run(self, args: list[str], cwd: Path) -> int:
        """Runs `git <args>` in *cwd* and returns its exit code."""
        ...

    def source_reachable(self, repo: str) -> bool:
        """Returns whether this machine's Git identity can read *repo*."""
        ...


class PipxInstall(Protocol):
    """How pipx holds one distribution."""

    @property
    def source(self) -> Path | None:
        """Returns the directory pipx was pointed at, or None for an index install."""
        ...

    @property
    def editable(self) -> bool:
        """Returns whether the install tracks a checkout."""
        ...


class PipxClient(Protocol):
    """Installs and upgrades Python command-line packages with pipx."""

    def available(self) -> bool:
        """Returns whether pipx can be run on this machine."""
        ...

    def install(self, pkg_dir: Path, *, editable: bool) -> int:
        """Installs *pkg_dir* over whatever is there and returns pipx's exit code."""
        ...

    def installed(self, name: str) -> PipxInstall | None:
        """Returns how pipx holds *name*, or None when it does not hold it."""
        ...

    def upgrade(self, name: str) -> int:
        """Upgrades *name* from the index and returns pipx's exit code."""
        ...


class AccountClient(Protocol):
    """The Sushi Account calls a command makes."""

    def start_device_login(self) -> DeviceCode:
        """Starts the device grant and returns the code the person approves."""
        ...

    def wait_for_token(self, code: DeviceCode, on_poll: Callable[[int], None] | None = None) -> object:
        """Waits until *code* is approved and stores the session."""
        ...

    def access_token(self) -> str | None:
        """Returns a live access token, or None when nobody is signed in."""
        ...

    def me(self) -> Account | None:
        """Returns the signed-in account, or None when nobody is signed in."""
        ...

    def licence_token(self, product: str) -> LicenceToken:
        """Returns the licence token *product* reads at start-up."""
        ...

    def resolve_release(self, product: str, platform: str, version: str | None = None) -> ReleaseInfo:
        """Returns where the *platform* release of *product* is downloaded from."""
        ...

    def logout(self) -> None:
        """Forgets the stored session."""
        ...


class ReleaseHost(Protocol):
    """Names the platform a release is downloaded for."""

    def platform(self) -> str:
        """Returns the platform string, such as ``windows-x64``."""
        ...


@dataclass(frozen=True)
class Ports:
    """The five ports one command runs against.

    Attributes:
        console: Where the command prints.
        git: What runs git.
        pipx: What runs pipx.
        account: Builds the Sushi Account client; called only when a command needs one.
        host: Names the platform a release is downloaded for.
    """

    console: ConsolePort
    git: GitClient
    pipx: PipxClient
    account: Callable[[], AccountClient]
    host: ReleaseHost

    @classmethod
    def machine(cls, console: ConsolePort | None = None) -> "Ports":
        """Returns the ports of this machine: the terminal, git, pipx, Sushi Account, the host.

        Args:
            console: The console to print through; :mod:`sushihub.console` when None.
        """
        from .. import console as hub_console
        from . import session
        from .git_ops import ProcessGit
        from .pipx import ProcessPipx
        from .releases import MachineHost

        return cls(console=console if console is not None else hub_console,
                   git=ProcessGit(), pipx=ProcessPipx(),
                   account=lambda: session.client(), host=MachineHost())
