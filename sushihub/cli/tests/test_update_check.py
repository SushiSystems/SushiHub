"""What Sushi ID says the latest release is, and what a refusal turns into."""

from __future__ import annotations

from sushistack.services.identity import SushiId
from sushistack.services.token_store import MemoryStore, Tokens
from sushistack.services.update_check import latest_release

from .test_identity import fake_id  # noqa: F401  the fake Sushi ID server fixture
from .test_identity import _signed_in


def test_names_the_latest_release_without_asking_for_a_version(fake_id):
    check = latest_release(_signed_in(fake_id), "sushiengine", "windows-x64")

    assert check.version == "1.4.2"
    assert check.reason is None
    assert "version" not in fake_id.state.resolved[-1]


def test_gives_the_reason_when_nobody_is_signed_in(fake_id):
    client = SushiId(fake_id.url, MemoryStore(), now=lambda: 0.0)

    check = latest_release(client, "sushiengine", "windows-x64")

    assert check.version is None
    assert "hub login" in check.reason


def test_gives_the_reason_when_the_account_holds_no_licence(fake_id):
    fake_id.state.licensed = set()

    check = latest_release(_signed_in(fake_id), "sushiengine", "windows-x64")

    assert check.version is None
    assert "licence" in check.reason


def test_gives_the_reason_when_sushi_id_is_unreachable():
    client = SushiId("http://127.0.0.1:9", MemoryStore(Tokens("access-1", "refresh-1", 1e12)),
                     now=lambda: 0.0)

    check = latest_release(client, "sushiengine", "windows-x64")

    assert check.version is None
    assert "unreachable" in check.reason

