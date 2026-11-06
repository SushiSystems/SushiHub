# test_dependency_fragment.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests what `hub` adds when it reads a fragment, and what it still refuses.

The format is `sushicore.deps_fragment`'s and is tested there. Here: the owner `hub` attaches,
that every fragment this package ships reads, and that a shape the reader cannot understand
stops `hub`. The reason is in docs/reference/MODULE_MANIFEST.md.
"""

from __future__ import annotations

from importlib.resources import files

import pytest

from sushihub.setup.dependency_source import (
    SHARED_OWNER,
    TomlDependencySource,
    packaged_manifests,
)

pytestmark = pytest.mark.medium

K_SHIPPED = sorted(path.name for path in files("sushihub").joinpath("manifests").iterdir()
                   if path.name.endswith(".deps.toml"))


def _source(tmp_path, text: str, owner: str) -> TomlDependencySource:
    """Write *text* as a fragment owned by *owner* and return the source that reads it."""
    path = tmp_path / "sushistack.deps.toml"
    path.write_text(text, encoding="utf-8")
    return TomlDependencySource([(path, owner)])


def test_every_dependency_carries_the_module_that_declared_it(tmp_path):
    """Ownership is `hub`'s question: the file says what, not who is asking."""
    deps = _source(tmp_path, """
[sdl2]
description = "Audio device backend."
linux_apt = ["libsdl2-dev"]
""", "sushidsp").all()

    assert [d.name for d in deps] == ["sdl2"]
    assert deps[0].owner == "sushidsp"
    assert deps[0].linux_apt == ["libsdl2-dev"]


def test_the_module_table_still_yields_depends_on(tmp_path):
    """`hub` reads the metadata table through the same reader as everything else."""
    source = _source(tmp_path, '[module]\ndepends_on = ["sushiruntime"]\n\n[hwloc]\n', "sushiblas")

    assert [d.name for d in source.all()] == ["hwloc"]
    assert source.depends_on("sushiblas") == ["sushiruntime"]


def test_a_shape_the_reader_refuses_still_stops_hub(tmp_path):
    """Delegating must not turn a refusal back into a silent skip."""
    source = _source(tmp_path, '[[dependency]]\nname = "sdl2"\n', "sushidsp")

    with pytest.raises(ValueError) as caught:
        source.all()

    assert str(tmp_path / "sushistack.deps.toml") in str(caught.value)


def test_a_dependency_that_names_no_owner_belongs_to_the_shared_set(tmp_path):
    """The packaged fragments have no module behind them; SHARED_OWNER says so."""
    deps = _source(tmp_path, "[cmake]\n", SHARED_OWNER).all()

    assert deps[0].owner == SHARED_OWNER


@pytest.mark.parametrize("fragment", K_SHIPPED)
def test_the_fragments_this_package_ships_all_read(fragment):
    """A shipped fragment that stopped parsing would break every install."""
    with packaged_manifests() as directory:
        deps = TomlDependencySource([(directory / fragment, fragment)]).all()

    assert deps, f"{fragment} declared nothing"
