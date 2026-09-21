"""How a `sushistack.deps.toml` fragment is read.

A fragment is written by hand in another repository, so the reader meets shapes
it did not choose. Until 2026-09-22 it skipped every top-level key that was not
a table, which is how sushidsp's whole fragment -- a required `sdl2` among it --
went unprovisioned without a word.
"""

from __future__ import annotations

import pytest

from sushistack.setup.dependency_source import _parse_manifest


def _fragment(tmp_path, text: str):
    """Write *text* as a fragment and return its path."""
    path = tmp_path / "sushistack.deps.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_one_table_per_dependency_is_the_shape(tmp_path):
    """Each top-level table becomes a dependency keyed by its name."""
    path = _fragment(tmp_path, """
[sdl2]
description = "Audio device backend."
required = true
linux_apt = ["libsdl2-dev"]
windows_vcpkg = ["sdl2"]
""")

    deps, depends_on = _parse_manifest(path, "sushidsp")

    assert [d.name for d in deps] == ["sdl2"]
    assert deps[0].required is True
    assert deps[0].linux_apt == ["libsdl2-dev"]
    assert depends_on == []


def test_the_module_table_is_metadata_rather_than_a_dependency(tmp_path):
    """[module] carries depends_on and never becomes a Dependency of its own."""
    path = _fragment(tmp_path, """
[module]
depends_on = ["sushiruntime"]

[hwloc]
description = "Topology."
""")

    deps, depends_on = _parse_manifest(path, "sushiblas")

    assert [d.name for d in deps] == ["hwloc"]
    assert depends_on == ["sushiruntime"]


def test_an_array_of_tables_is_refused_rather_than_skipped(tmp_path):
    """The shape that used to lose a fragment silently now names itself."""
    path = _fragment(tmp_path, """
[[dependency]]
name = "sdl2"
required = true
linux_apt = ["libsdl2-dev"]
""")

    with pytest.raises(ValueError) as caught:
        _parse_manifest(path, "sushidsp")

    assert "dependency" in str(caught.value)
    assert str(path) in str(caught.value)


def test_a_scalar_at_the_top_level_is_refused_too(tmp_path):
    """Any non-table top-level key is a shape the reader does not understand."""
    path = _fragment(tmp_path, 'version = "1"\n\n[sdl2]\ndescription = "x"\n')

    with pytest.raises(ValueError):
        _parse_manifest(path, "sushidsp")


def test_the_repository_fragments_all_parse(tmp_path):
    """Every fragment this package ships reads without raising."""
    from sushistack.setup.dependency_source import packaged_manifests

    with packaged_manifests() as directory:
        for fragment in sorted(directory.glob("*.deps.toml")):
            deps, _ = _parse_manifest(fragment, fragment.stem)
            assert deps, f"{fragment.name} declared nothing"
