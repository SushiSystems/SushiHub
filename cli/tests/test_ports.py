# test_ports.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The in-memory adapters keep the promises of their ports, and commands reach the ports."""

from __future__ import annotations

from pathlib import Path

import pytest
from sushicore.console_memory import RecordingConsole

from sushihub.errors import SushiAccountError
from sushihub.services import binary, session
from sushihub.services.identity import Account, Licence, NoLicence, NoRelease, ReleaseInfo
from sushihub.services.memory.account import DEVICE_CODE, InMemoryAccount
from sushihub.services.memory.git import GitCall, InMemoryGit
from sushihub.services.memory.host import FixedHost
from sushihub.services.memory.pipx import InMemoryPipx
from sushihub.services.memory.ports import memory_ports
from sushihub.services.pipx import Install

pytestmark = pytest.mark.small

ACCOUNT = Account("acc-1", "ada@example.com", (Licence("sushiengine", "account", None),))
RELEASE = ReleaseInfo("1.4.2", "linux-x64", "https://cdn.test/e.zip", "00", 3, "")


def test_git_records_each_command_with_its_folder():
    """Every command is kept, in order, with the folder it was to run in."""
    git = InMemoryGit()
    git.run(["pull", "--ff-only"], Path("a"))
    git.run(["fetch"], Path("b"))
    assert git.calls == [GitCall(("pull", "--ff-only"), Path("a")), GitCall(("fetch",), Path("b"))]


def test_git_answers_scripted_codes_then_zero():
    """A scripted exit code answers the next command; an unscripted one exits 0."""
    git = InMemoryGit().script(128)
    assert [git.run(["clone"], Path(".")), git.run(["clone"], Path("."))] == [128, 0]


@pytest.mark.parametrize("reached, expected", [(True, True), (False, False)])
def test_git_reaches_only_a_repository_it_was_told_of(reached, expected):
    """A repository is reachable only once it was named to reach()."""
    git = InMemoryGit()
    if reached:
        git.reach("https://git.test/engine")
    assert git.source_reachable("https://git.test/engine") is expected


@pytest.mark.parametrize("version, expected", [("v1", "a" * 40), ("v2", None)])
def test_git_finds_only_a_tag_it_was_told_of(version, expected):
    """A tag points at the commit named to tag() and is not found otherwise."""
    git = InMemoryGit().tag("https://git.test/engine", "v1", "a" * 40)
    assert git.tag_commit("https://git.test/engine", version) == expected


def test_pipx_reports_the_install_it_was_given():
    """installed() answers from the table, None for a name not in it."""
    held = Install(Path("/src/hub"))
    pipx = InMemoryPipx(held={"sushihub": held})
    assert (pipx.installed("sushihub"), pipx.installed("other")) == (held, None)


def test_pipx_records_an_install_and_returns_its_exit_code():
    """An install is kept with its editable flag and answers the configured code."""
    pipx = InMemoryPipx(exit_code=2)
    code = pipx.install(Path("mod/cli"), editable=True)
    assert (code, pipx.installs) == (2, [(Path("mod/cli"), True)])


def test_pipx_records_an_upgrade():
    """An upgrade is kept by name."""
    pipx = InMemoryPipx()
    pipx.upgrade("sushihub")
    assert pipx.upgrades == ["sushihub"]


def test_pipx_reports_the_availability_it_was_given():
    """available() is what the adapter was built with."""
    assert InMemoryPipx(available=False).available() is False


def test_account_signed_out_has_no_token_and_no_account():
    """A signed-out client gives neither a token nor an account."""
    account = InMemoryAccount(ACCOUNT)
    assert (account.access_token(), account.me()) == (None, None)


@pytest.mark.parametrize("call", [
    lambda account: account.resolve_release("sushiengine", "linux-x64"),
    lambda account: account.licence_token("sushiengine"),
])
def test_account_signed_out_refuses_a_session_call(call):
    """A call that needs a session raises SushiAccountError while nobody is signed in."""
    with pytest.raises(SushiAccountError):
        call(InMemoryAccount(ACCOUNT))


def test_account_login_reports_one_poll_and_signs_in():
    """The login polls once and the account is signed in afterwards."""
    account = InMemoryAccount(ACCOUNT)
    polls: list[int] = []
    account.wait_for_token(account.start_device_login(), on_poll=polls.append)
    assert (polls, account.me()) == ([1], ACCOUNT)


def test_account_login_raises_the_refusal_it_was_given():
    """A refused login raises the given error and leaves nobody signed in."""
    account = InMemoryAccount(ACCOUNT, refusal=SushiAccountError("refused"))
    with pytest.raises(SushiAccountError):
        account.wait_for_token(DEVICE_CODE)


def test_account_logout_forgets_the_session():
    """After logout nobody is signed in."""
    account = InMemoryAccount(ACCOUNT, signed_in=True)
    account.logout()
    assert account.signed_in is False


@pytest.mark.parametrize("call, error", [
    (lambda account: account.resolve_release("sushiengine", "windows-x64"), NoRelease),
    (lambda account: account.licence_token("sushiengine"), NoLicence),
])
def test_account_refuses_what_its_tables_do_not_hold(call, error):
    """A release or a licence the tables lack raises the real client's error."""
    with pytest.raises(error):
        call(InMemoryAccount(ACCOUNT, signed_in=True,
                             releases={("sushiengine", "linux-x64"): RELEASE}))


def test_account_resolves_a_release_it_holds():
    """A release in the table is returned for its product and platform."""
    account = InMemoryAccount(ACCOUNT, signed_in=True,
                              releases={("sushiengine", "linux-x64"): RELEASE})
    assert account.resolve_release("sushiengine", "linux-x64") == RELEASE


def test_host_names_the_platform_it_was_given():
    """A fixed host names its platform whatever the machine is."""
    assert FixedHost("windows-x64").platform() == "windows-x64"


def test_whoami_reads_the_account_through_the_port():
    """`hub whoami` prints the account the account port holds."""
    out = RecordingConsole()
    session.whoami(ports=memory_ports(console=out, account=InMemoryAccount(ACCOUNT, signed_in=True)))
    assert out.has_call("table")


def test_logout_signs_out_through_the_port():
    """`hub logout` clears the session of the account port."""
    account = InMemoryAccount(ACCOUNT, signed_in=True)
    session.logout(ports=memory_ports(account=account))
    assert account.signed_in is False


def test_a_binary_add_without_a_session_is_refused_through_the_console_port(tmp_path):
    """A binary add with nobody signed in fails and says why on the console port."""
    out = RecordingConsole()
    binary.add("sushiengine", tmp_path / "engine", True, ports=memory_ports(console=out))
    assert out.texts("error") == ["sushiengine: a binary install needs a Sushi Account licence. "
                                  "Run `hub login` first."]
