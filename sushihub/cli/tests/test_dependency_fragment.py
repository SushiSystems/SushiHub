"""What `hub` adds when it reads a fragment, and what it still refuses.

The format itself is `sushicore.deps_fragment`'s and is tested there. What is
left here is `hub`'s own part — the owner it attaches — and the two contracts a
caller of `hub` depends on: the fragments this package ships all read, and a
shape the reader cannot understand still stops `hub` rather than being skipped.
That silence is what lost sushidsp's fragment until 2026-09-22.
"""

from __future__ import annotations

import pytest

from sushistack.setup.dependency_source import SHARED_OWNER, _parse_manifest


def _fragment(tmp_path, text: str):
    """Write *text* as a fragment and return its path."""
    path = tmp_path / "sushistack.deps.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_every_dependency_carries_the_module_that_declared_it(tmp_path):
    """Ownership is `hub`'s question: the file says what, not who is asking."""
    path = _fragment(tmp_path, """
[sdl2]
description = "Audio device backend."
linux_apt = ["libsdl2-dev"]
""")

    deps, _ = _parse_manifest(path, "sushidsp")

    assert [d.name for d in deps] == ["sdl2"]
    assert deps[0].owner == "sushidsp"
    assert deps[0].linux_apt == ["libsdl2-dev"]


def test_the_module_table_still_yields_depends_on(tmp_path):
    """`hub` reads the metadata table through the same reader as everything else."""
    path = _fragment(tmp_path, '[module]\ndepends_on = ["sushiruntime"]\n\n[hwloc]\n')

    deps, depends_on = _parse_manifest(path, "sushiblas")

    assert [d.name for d in deps] == ["hwloc"]
    assert depends_on == ["sushiruntime"]


def test_a_shape_the_reader_refuses_still_stops_hub(tmp_path):
    """Delegating must not turn a refusal back into a silent skip."""
    path = _fragment(tmp_path, '[[dependency]]\nname = "sdl2"\n')

    with pytest.raises(ValueError) as caught:
        _parse_manifest(path, "sushidsp")

    assert str(path) in str(caught.value)


def test_a_dependency_that_names_no_owner_belongs_to_the_shared_set(tmp_path):
    """The packaged fragments have no module behind them; SHARED_OWNER says so."""
    path = _fragment(tmp_path, "[cmake]\n")

    deps, _ = _parse_manifest(path, SHARED_OWNER)

    assert deps[0].owner == SHARED_OWNER


def test_the_fragments_this_package_ships_all_read():
    """A shipped fragment that stopped parsing would break every install."""
    from sushistack.setup.dependency_source import packaged_manifests

    with packaged_manifests() as directory:
        for fragment in sorted(directory.glob("*.deps.toml")):
            deps, _ = _parse_manifest(fragment, fragment.stem)
            assert deps, f"{fragment.name} declared nothing"
