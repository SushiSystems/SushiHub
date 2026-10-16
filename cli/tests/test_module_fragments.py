# test_module_fragments.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Where a module's dependency fragment is, and which libraries the workspace pins."""

from __future__ import annotations

from sushihub.services import module_fragments

K_COMMIT = "0123456789abcdef0123456789abcdef01234567"


def test_a_manifest_names_the_fragment(tmp_path):
    """sushi-module.toml's fragment key wins over the catalog's default."""
    checkout = tmp_path / "sushilog"
    checkout.mkdir()
    (checkout / "sushi-module.toml").write_text(
        '[module]\nname = "sushilog"\nalias = "sl"\ndistribution = "source"\n'
        'fragment = "deps/fragment.toml"\n', encoding="utf-8")
    assert module_fragments.fragment_of("sushilog", checkout) == checkout / "deps" / "fragment.toml"


def test_without_a_manifest_the_catalog_path_is_used(tmp_path):
    """A catalog module with no manifest keeps its fragment under cli/."""
    assert (module_fragments.fragment_of("sushiruntime", tmp_path)
            == tmp_path / "cli" / "sushistack.deps.toml")


def test_workspace_pins_yields_each_module_and_its_pin(tmp_path, monkeypatch):
    """Every pin of every present module is yielded with the fragment it came from."""
    checkout = tmp_path / "sushiruntime"
    fragment = checkout / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text('[module]\ndepends_on = ["sushilog"]\n\n'
                        f'[sushi.sushilog]\nversion = "v0.1.0"\ncommit = "{K_COMMIT}"\n',
                        encoding="utf-8")
    monkeypatch.setattr(module_fragments, "present_modules", lambda root: {"sushiruntime": checkout})
    found = [(name, path, pin.name, pin.version) for name, path, pin in
             module_fragments.workspace_pins(tmp_path)]
    assert found == [("sushiruntime", fragment, "sushilog", "v0.1.0")]
