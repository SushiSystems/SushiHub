"""The payload `hub status` ends with, composed from the readers that look at disk.

Each fact has one reader: presence and the release manifest in
:mod:`.presence`, the licence file in :mod:`.licence_file`, a checkout in
:mod:`.git_state`, `hub` itself in :mod:`.hub_install`. This module only puts
their answers where ``sushihub/contract/status.schema.json`` says they go.
With ``check_updates`` it fetches every checkout and asks Sushi Account about every
binary install first, through :mod:`.git_state` and :mod:`.update_check`, and
collects what failed as warnings instead of printing them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import console
from ..config import deps_dir, workspace_root
from . import git_state, licence_file, links, session
from .hub_install import read_hub_install
from .identity import SushiAccount
from .presence import Presence, describe, module_dir, presence_of, read_release, workspace_modules
from .update_check import latest_release


@dataclass
class StatusReport:
    """The status payload and the warnings an online check left behind."""

    payload: dict
    warnings: list[str] = field(default_factory=list)


def _source(path: Path, check_updates: bool, warnings: list[str], label: str) -> dict | None:
    """Fetch *path* when checking updates, then read its git state as a payload object."""
    if check_updates and git_state.read_git_state(path) is not None:
        if not git_state.fetch(path):
            warnings.append(f"{label}: git fetch failed; ahead and behind are from the last fetch.")
    state = git_state.read_git_state(path)
    return state.as_payload() if state else None


class _LazyClient:
    """Builds the Sushi Account client the first time a binary install asks for it."""

    def __init__(self, factory: Callable[[], SushiAccount]) -> None:
        """Remember *factory* without calling it."""
        self._factory = factory
        self._client: SushiAccount | None = None

    def get(self) -> SushiAccount:
        """Return the client, building it on the first call."""
        if self._client is None:
            self._client = self._factory()
        return self._client


def _module_row(root: Path, name: str, linked: dict[str, str], check_updates: bool,
                client: _LazyClient, warnings: list[str]) -> dict:
    """Build the payload row of module *name*."""
    state = presence_of(root, name, linked)
    location, text = describe(root, name, linked)
    path = module_dir(root, name, linked)
    row = {"name": name, "location": location, "state": text, "presence": state.value,
           "version": None, "source": None, "binary": None, "latest_version": None}

    if state in (Presence.CLONED, Presence.LINKED):
        row["source"] = _source(path, check_updates, warnings, name)
    elif state is Presence.BINARY:
        release = read_release(path)
        if release is not None:
            row["version"] = release.version
            row["binary"] = {"platform": release.platform,
                             "licence_expires_at": licence_file.read_licence_expiry(path)}
            if check_updates:
                check = latest_release(client.get(), name, release.platform)
                row["latest_version"] = check.version
                if check.reason:
                    warnings.append(f"{name}: {check.reason}")
    return row


def build_status(check_updates: bool = False, *, home: Path | None = None,
                 client_factory: Callable[[], SushiAccount] = session.client) -> StatusReport:
    """Collect the workspace, `hub`, every module and the dependency tree.

    Args:
        check_updates: Fetch every checkout and ask Sushi Account about every binary
            install before reading; the only form that touches the network.
        home: The home directory the alias is searched under; the user's own
            when None.
        client_factory: Builds the Sushi Account client, called at most once and
            only when an update check meets a binary install.

    Returns:
        The payload ``status.schema.json`` describes, and one warning per check
        that could not be answered.
    """
    root = workspace_root()
    deps = deps_dir()
    warnings: list[str] = []
    client = _LazyClient(client_factory)
    linked = links.registered()

    hub = read_hub_install(home or Path.home())
    hub["source"] = _source(root, check_updates, warnings, "hub")
    hub["latest_version"] = None

    known, unreadable = workspace_modules(root, linked)
    warnings.extend(unreadable)
    rows = [_module_row(root, name, linked, check_updates, client, warnings)
            for name in known]

    payload = {
        "workspace": str(root),
        "checked_updates": check_updates,
        "hub": hub,
        "modules": rows,
        "dependencies": {"path": str(deps), "present": deps.is_dir() and any(deps.iterdir())},
    }
    return StatusReport(payload, warnings)


def _branch_cell(source: dict | None) -> str:
    """Return a checkout's branch and its distance from upstream as one table cell."""
    if not source or not source["branch"]:
        return "—"
    counts = [f"{sign}{source[key]}" for key, sign in (("ahead", "+"), ("behind", "-"))
              if source[key]]
    return " ".join([source["branch"], *counts])


def render(payload: dict) -> int:
    """Print the status *payload* that :func:`build_status` built. Return exit code."""
    console.header("SushiStack Status")
    console.info(f"Workspace: {payload['workspace']}")
    console.table(
        ["Module", "Location", "State", "Branch"],
        [[module["name"], module["location"] or "—",
          "—" if module["state"] == "absent" else module["state"],
          _branch_cell(module["source"])]
         for module in payload["modules"]],
        title="SushiStack Status",
    )
    deps = payload["dependencies"]
    if deps["present"]:
        console.info(f"Dependencies: {deps['path']} (present). Verify with `hub doctor`.")
    else:
        console.info(f"Dependencies: {deps['path']} (empty). Provision with `hub install`.")
    return 0
