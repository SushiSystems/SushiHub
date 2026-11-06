# test_add_binary.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Choosing between the source and the binary, and what the binary path writes."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

from sushihub.services import binary, licence_file, modules
from sushihub.services.catalog import CATALOG
from sushihub.services.identity import Account, LicenceToken, ReleaseInfo
from sushihub.services.licence_file import LICENCE_FILE
from sushihub.services.memory.account import InMemoryAccount
from sushihub.services.memory.git import InMemoryGit
from sushihub.services.memory.ports import DEFAULT_PLATFORM, memory_ports
from sushihub.services.presence import RELEASE_MANIFEST
from sushihub.services.token_store import CredentialStoreError

from .support.console_text import said
from .support.release_files import binary_install, release_members, zip_bytes

pytestmark = pytest.mark.medium

LICENCE_EXPIRY = "2026-10-05T00:00:00Z"
ACCOUNT = Account("acc-1", "ada@example.com", ())


def engine_account(served, version: str = "1.4.2", *, signed_in: bool = True,
                   licensed: bool = True, sha256: str | None = None) -> InMemoryAccount:
    """Build an account whose release of sushiengine is a zip file written under *served*."""
    served.mkdir(exist_ok=True)
    blob = zip_bytes(release_members(version=version))
    archive = served / "sushiengine.zip"
    archive.write_bytes(blob)
    release = ReleaseInfo(version, DEFAULT_PLATFORM, archive.as_uri(),
                          sha256 or hashlib.sha256(blob).hexdigest(), len(blob), "")
    licences = {"sushiengine": LicenceToken("licence-jwt", LICENCE_EXPIRY)} if licensed else {}
    return InMemoryAccount(ACCOUNT, signed_in=signed_in, licences=licences,
                           releases={("sushiengine", DEFAULT_PLATFORM): release})


def installed_version(root) -> str:
    """Read the version the install at *root* reports."""
    return json.loads((root / RELEASE_MANIFEST).read_text(encoding="utf-8"))["version"]


def jwt(expiry: int) -> str:
    """Build a token whose payload names *expiry* as its ``exp`` claim."""
    def segment(payload: dict) -> str:
        blob = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8"))
        return blob.decode("ascii").rstrip("=")
    return f"{segment({'alg': 'EdDSA'})}.{segment({'exp': expiry})}.signature"


def test_add_clones_sushiengine_when_its_repository_answers(workspace, out):
    """A module whose repository answers is cloned, and nothing else is run."""
    git = InMemoryGit().reach(CATALOG["sushiengine"].repo)
    rc = modules.add(["sushiengine"], provision=lambda dry_run: 0,
                     ports=memory_ports(console=out, git=git))
    assert (rc, [call.args[0] for call in git.calls]) == (0, ["clone"])


def test_add_installs_the_release_when_the_repository_is_out_of_reach(workspace, out):
    """The unpacked release and its licence land in the module directory."""
    account = engine_account(workspace / "served")
    modules.add(["sushiengine"], provision=lambda dry_run: 0,
                ports=memory_ports(console=out, account=account))
    root = workspace / "sushiengine"
    assert (installed_version(root), (root / LICENCE_FILE).read_text(encoding="utf-8")) == (
        "1.4.2", "licence-jwt")


def test_add_of_a_release_does_not_run_the_provision_pipeline(workspace, out):
    """A release brings its own dependencies, so nothing is provisioned."""
    provisioned = []
    account = engine_account(workspace / "served")
    rc = modules.add(["sushiengine"], provision=lambda dry_run: provisioned.append(dry_run),
                     ports=memory_ports(console=out, account=account))
    assert (rc, provisioned) == (0, [])


def test_add_of_a_release_says_what_it_installed(workspace, out):
    """The success line names the installed version."""
    account = engine_account(workspace / "served")
    modules.add(["sushiengine"], provision=lambda dry_run: 0,
                ports=memory_ports(console=out, account=account))
    assert said(out, "installed binary 1.4.2")


def test_add_binary_installs_it_even_when_the_source_is_in_reach(workspace, out):
    """--binary installs the release without cloning, though the repository answers."""
    git = InMemoryGit().reach(CATALOG["sushiengine"].repo)
    account = engine_account(workspace / "served")
    rc = modules.add(["sushiengine"], binary=True, provision=lambda dry_run: 0,
                     ports=memory_ports(console=out, git=git, account=account))
    assert (rc, installed_version(workspace / "sushiengine"), git.calls) == (0, "1.4.2", [])


def test_add_names_both_ways_in_when_neither_is_open(workspace, out):
    """With no source and no session the error names a Git identity and `hub login`."""
    rc = modules.add(["sushiengine"], provision=lambda dry_run: 0,
                     ports=memory_ports(console=out))
    assert rc == 1
    assert said(out, "a Git identity with access") and said(out, "`hub login`")
    assert not (workspace / "sushiengine").exists()


def test_add_binary_without_a_session_asks_for_the_login_alone(workspace, out):
    """--binary with nobody signed in asks only for the login."""
    rc = modules.add(["sushiengine"], binary=True, provision=lambda dry_run: 0,
                     ports=memory_ports(console=out))
    assert rc == 1
    assert said(out, "Run `hub login` first.")
    assert not said(out, "a Git identity with access")


def test_add_binary_refuses_a_module_that_is_not_sold(workspace, out):
    """--binary on a module the catalog does not sell as a binary is refused, nothing written."""
    rc = modules.add(["sushiruntime"], binary=True, provision=lambda dry_run: 0,
                     ports=memory_ports(console=out))
    assert rc == 1
    assert said(out, "only sushiengine is sold as a binary")
    assert not (workspace / "sushiruntime").exists()


def test_add_reports_a_licence_the_account_does_not_hold(workspace, out):
    """An account with no licence for sushiengine is told so and the install fails."""
    account = engine_account(workspace / "served", licensed=False)
    rc = modules.add(["sushiengine"], provision=lambda dry_run: 0,
                     ports=memory_ports(console=out, account=account))
    assert rc == 1
    assert said(out, "no live licence")


def test_add_refuses_a_download_whose_hash_does_not_match(workspace, out):
    """A download that differs from the declared sha256 is refused and nothing is left."""
    account = engine_account(workspace / "served", sha256="0" * 64)
    rc = modules.add(["sushiengine"], provision=lambda dry_run: 0,
                     ports=memory_ports(console=out, account=account))
    assert rc == 1
    assert said(out, "sha256")
    assert not (workspace / "sushiengine").exists()


def test_add_dry_run_says_it_would_install_the_release(workspace, out):
    """A dry run names the release install and writes nothing."""
    rc = modules.add(["sushiengine"], dry_run=True, provision=lambda dry_run: 0,
                     ports=memory_ports(console=out))
    assert rc == 0
    assert said(out, "would install its release")
    assert not (workspace / "sushiengine").exists()


def test_update_says_a_binary_install_is_already_the_latest(workspace, out):
    """An install at the latest release is reported as such and rewrites nothing."""
    binary_install(workspace / "sushiengine", "1.4.2")
    account = engine_account(workspace / "served", "1.4.2")
    rc = modules.update(["sushiengine"], ports=memory_ports(console=out, account=account))
    assert rc == 0
    assert said(out, "binary 1.4.2 is the latest release.")
    assert not (workspace / "sushiengine" / LICENCE_FILE).exists()


def test_update_downloads_a_newer_release_and_writes_the_licence_again(workspace, out):
    """A newer release replaces the install and the licence is written beside it."""
    binary_install(workspace / "sushiengine", "1.4.2")
    account = engine_account(workspace / "served", "1.5.0")
    rc = modules.update(["sushiengine"], ports=memory_ports(console=out, account=account))
    root = workspace / "sushiengine"
    assert (rc, installed_version(root), (root / LICENCE_FILE).read_text(encoding="utf-8")) == (
        0, "1.5.0", "licence-jwt")


def test_update_asks_for_a_login_before_refreshing_a_binary_install(workspace, out):
    """With nobody signed in, update of a binary install asks for the login."""
    binary_install(workspace / "sushiengine", "1.4.2")
    rc = modules.update(["sushiengine"], ports=memory_ports(console=out))
    assert rc == 1
    assert said(out, "Run `hub login` first.")


def test_write_licence_returns_the_expiry_and_writes_the_bare_token(tmp_path):
    """The licence file holds the token alone, and the expiry comes back."""
    account = InMemoryAccount(ACCOUNT, signed_in=True,
                              licences={"sushiengine": LicenceToken("licence-jwt", LICENCE_EXPIRY)})
    expires_at = licence_file.write_licence(tmp_path, account, "sushiengine")
    assert (expires_at, (tmp_path / LICENCE_FILE).read_text(encoding="utf-8")) == (
        LICENCE_EXPIRY, "licence-jwt")


@pytest.mark.small
@pytest.mark.parametrize("token, expiry", [
    (jwt(1790000000), "2026-09-21T14:13:20+00:00"),
    ("not a token", None),
    ("header.eyJzdWIiOiAiYSJ9.sig", None),
])
def test_licence_expiry_reads_the_exp_claim_of_a_jwt(token, expiry):
    """The exp claim becomes an ISO time; a text that is not a JWT, or names no exp, gives None."""
    assert licence_file.licence_expiry(token) == expiry


def test_read_licence_expiry_is_none_without_a_file(tmp_path):
    assert licence_file.read_licence_expiry(tmp_path) is None


class UnusableAccount(InMemoryAccount):
    """An account whose credential store cannot be read, as on a machine with no keyring backend."""

    def access_token(self) -> str | None:
        """Fails the way the keyring store does when the backend is missing."""
        raise CredentialStoreError("The credential store is unusable: no backend.")


@pytest.mark.parametrize("act", [
    lambda dest, ports: binary.add("sushiengine", dest, requested=True, ports=ports),
    lambda dest, ports: binary.update("sushiengine", dest, ports=ports),
])
def test_a_binary_install_reports_a_credential_store_it_cannot_read(workspace, out, act):
    """add and update name the module, print the failure once and return False."""
    ports = memory_ports(console=out, account=UnusableAccount(ACCOUNT))
    assert act(workspace / "sushiengine", ports) is False
    assert out.texts("error") == ["sushiengine: The credential store is unusable: no backend."]
