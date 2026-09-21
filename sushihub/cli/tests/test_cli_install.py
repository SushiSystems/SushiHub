"""How a module's own CLI is installed and where sushicore is injected from."""

from __future__ import annotations

import pytest

from sushistack.services import modules

from .test_presence import Recorder


class _Runs:
    """Stands in for subprocess.run and records each command with a fixed return code."""

    def __init__(self, code: int = 0) -> None:
        """Start with no recorded commands and the return code to report."""
        self.commands: list[list[str]] = []
        self._code = code

    def __call__(self, args, **kwargs):
        """Record one command and report the fixed return code."""
        self.commands.append(list(args))
        return type("Completed", (), {"returncode": self._code})()


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line the CLI install prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


@pytest.fixture
def checkout(tmp_path):
    """Build a module checkout carrying a cli/ package pipx could install."""
    cli = tmp_path / "sushiruntime" / "cli"
    cli.mkdir(parents=True)
    (cli / "pyproject.toml").write_text("", encoding="utf-8")
    return tmp_path / "sushiruntime"


@pytest.fixture
def root(tmp_path):
    """Build a workspace root carrying a sushicore distribution to inject."""
    core = tmp_path / modules.SUSHICORE_NAME
    core.mkdir()
    (core / "pyproject.toml").write_text("", encoding="utf-8")
    return tmp_path


def test_sushicore_is_found_at_a_fixed_path_under_the_root(root):
    """Resolves sushicore to <root>/sushicore when that path carries a pyproject."""
    assert modules.sushicore_dir(root) == root / modules.SUSHICORE_NAME


def test_sushicore_is_none_when_the_checkout_is_partial(tmp_path):
    """Treats a sushicore directory without a pyproject.toml as missing."""
    (tmp_path / modules.SUSHICORE_NAME).mkdir()
    assert modules.sushicore_dir(tmp_path) is None


def test_a_module_without_a_cli_package_is_skipped(tmp_path, recorder, root, monkeypatch):
    """Skips pipx and succeeds when the checkout carries no cli/pyproject.toml."""
    monkeypatch.setattr(modules, "_pipx_cmd",
                        lambda: pytest.fail("pipx was looked for"))
    assert modules._install_module_cli("sushiai", tmp_path / "sushiai", root) is True
    assert recorder.said("sushiai: no cli/ package to install; skipping CLI install.")


def test_a_missing_pipx_is_a_warning(checkout, root, recorder, monkeypatch):
    """Reports failure and names the command to run later when pipx is missing."""
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: None)
    assert modules._install_module_cli("sushiruntime", checkout, root) is False
    assert recorder.said("sushiruntime: pipx not found; skipping CLI install. Install "
                         f"it later with `pipx install {checkout / 'cli'}`.")


def test_a_missing_sushicore_stops_after_the_install(checkout, tmp_path, recorder,
                                                     monkeypatch):
    """Installs the CLI with pipx, then reports the absent sushicore and injects nothing."""
    runs = _Runs()
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: ["pipx"])
    monkeypatch.setattr(modules, "subprocess", type("S", (), {"run": runs}))
    assert modules._install_module_cli("sushiruntime", checkout, tmp_path) is False
    assert len(runs.commands) == 1
    assert runs.commands[0][:2] == ["pipx", "install"]
    assert recorder.said(f"sushiruntime: sushicore is missing from "
                         f"{tmp_path / modules.SUSHICORE_NAME}; the CLI may fail to "
                         "start. It ships with this repository -- `git checkout -- "
                         "sushicore` to restore it.")


def test_the_happy_path_installs_then_injects(checkout, root, recorder, monkeypatch):
    """Installs the module's cli/ with pipx and injects sushicore as an editable distribution."""
    runs = _Runs()
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: ["pipx"])
    monkeypatch.setattr(modules, "subprocess", type("S", (), {"run": runs}))
    monkeypatch.setattr(modules, "_cli_package_name", lambda cli_dir, name: "sushiruntime-cli")
    assert modules._install_module_cli("sushiruntime", checkout, root) is True
    assert runs.commands[0] == ["pipx", "install", "--force", str(checkout / "cli")]
    assert runs.commands[1] == ["pipx", "inject", "sushiruntime-cli", "--editable",
                                str(root / modules.SUSHICORE_NAME)]
