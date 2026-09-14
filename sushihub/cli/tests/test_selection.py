"""A toolchain is selected because a present module asked for it."""

from sushistack.setup.selection import ToolchainSelection, selection_from_source

from .conftest import MemorySource, dep


def test_empty_workspace_selects_no_toolchain_but_keeps_the_gpu_on():
    sel = selection_from_source(MemorySource([dep("cmake"), dep("ninja")]))
    assert sel == ToolchainSelection(False, False, False, True)


def test_runtime_fragment_turns_its_toolchains_on():
    src = MemorySource([dep("cmake"), dep("intel-llvm", "sushiruntime")])
    sel = selection_from_source(src)
    assert sel.install_intel_llvm and sel.gpu
    assert not sel.install_acpp and not sel.oneapi


def test_the_gpu_is_on_with_no_module_declaring_a_gpu_dependency():
    src = MemorySource([dep("intel-llvm", "sushiruntime"), dep("oneapi", "sushiruntime")])
    assert selection_from_source(src).gpu


def test_a_shared_fragment_cannot_select_a_toolchain():
    sel = selection_from_source(MemorySource([dep("intel-llvm", "shared")]))
    assert not sel.install_intel_llvm


def test_components_lists_selected_keys_in_catalogue_order():
    src = MemorySource([dep("oneapi", "sushiruntime"), dep("intel-llvm", "sushiruntime")])
    assert selection_from_source(src).components() == ["intel-llvm", "oneapi", "gpu"]


def test_merged_applies_known_keys_only():
    sel = ToolchainSelection(False, False, False, False).merged({"gpu": True, "bogus": True})
    assert sel.gpu and sel.as_dict() == {"install_intel_llvm": False, "install_acpp": False,
                                         "oneapi": False, "gpu": True}


def test_build_pipeline_defaults_to_the_derived_selection(fake_cfg):
    from sushistack.setup.factory import build_pipeline
    src = MemorySource([dep("cmake"), dep("intel-llvm", "sushiruntime")])
    _pipeline, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[])
    assert ctx.install_intel_llvm and not ctx.install_acpp and not ctx.oneapi and ctx.gpu


def test_build_pipeline_merges_an_explicit_selection_over_the_derived_one(fake_cfg):
    from sushistack.setup.factory import build_pipeline
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    _p, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[],
                             selection={"install_intel_llvm": False, "oneapi": True})
    assert not ctx.install_intel_llvm and ctx.oneapi


def test_a_shipped_fragment_is_owned_by_the_name_in_its_filename():
    from pathlib import Path

    from sushistack.setup.dependency_source import SHARED_OWNER, _owner_for_shipped

    assert _owner_for_shipped(Path("manifests/base.deps.toml")) == SHARED_OWNER
    assert _owner_for_shipped(Path("manifests/gui.deps.toml")) == "gui"


def test_build_pipeline_honours_the_gpu_turned_off_in_customize(fake_cfg):
    from sushistack.setup.factory import build_pipeline
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    _p, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[],
                             selection={"gpu": False})
    assert not ctx.gpu
