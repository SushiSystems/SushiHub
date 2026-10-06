# test_selection.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A toolchain is selected because a present module requires it and the machine lacks it."""

import pytest
from sushicore.provision import probe
from sushicore.provision.manifests import base_fragment
from sushicore.provision.pipeline import ToolchainSelection

from sushihub.setup.dependency_source import SHARED_OWNER, manifest_sources
from sushihub.setup.factory import derived_selection

from .conftest import MemorySource, dep


@pytest.fixture
def bare_machine(monkeypatch):
    """Report no SYCL toolchain on this machine."""
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", False, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])


def _runtime() -> MemorySource:
    """Return a source declaring the runtime's three SYCL toolchains."""
    return MemorySource([dep("cmake")] + [
        dep(name, "sushiruntime", provides="sycl-toolchain")
        for name in ("intel-llvm", "adaptivecpp", "oneapi")])


def test_empty_workspace_selects_no_toolchain_but_keeps_the_gpu_on(fake_cfg, bare_machine):
    sel = derived_selection(MemorySource([dep("cmake"), dep("ninja")]), fake_cfg)
    assert sel == ToolchainSelection(False, False, False, True)


def test_a_bare_install_selects_one_sycl_toolchain(fake_cfg, bare_machine):
    sel = derived_selection(_runtime(), fake_cfg)
    assert (sel.install_intel_llvm, sel.install_acpp, sel.oneapi, sel.gpu) == (
        True, False, False, True)


def test_a_present_toolchain_selects_no_download(fake_cfg, monkeypatch):
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", False, ""), ("adaptivecpp", False, ""), ("oneapi", True, "")])
    sel = derived_selection(_runtime(), fake_cfg)
    assert not (sel.install_intel_llvm or sel.install_acpp or sel.oneapi)


def test_a_shared_fragment_cannot_select_a_toolchain(fake_cfg, bare_machine):
    sel = derived_selection(MemorySource([dep("intel-llvm", "shared")]), fake_cfg)
    assert not sel.install_intel_llvm


def test_the_base_fragment_comes_from_sushicore():
    assert manifest_sources()[0] == (base_fragment(), SHARED_OWNER)


def test_merged_applies_known_keys_only():
    sel = ToolchainSelection(False, False, False, False).merged({"gpu": True, "bogus": True})
    assert sel.gpu and sel.as_dict() == {"install_intel_llvm": False, "install_acpp": False,
                                         "oneapi": False, "gpu": True}


def test_build_pipeline_defaults_to_the_derived_selection(fake_cfg, bare_machine):
    from sushihub.setup.factory import build_pipeline
    src = MemorySource([dep("cmake"), dep("intel-llvm", "sushiruntime")])
    _pipeline, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[])
    sel = ctx.selection
    assert sel.install_intel_llvm and not sel.install_acpp and not sel.oneapi and ctx.gpu


def test_build_pipeline_merges_an_explicit_selection_over_the_derived_one(fake_cfg, bare_machine):
    from sushihub.setup.factory import build_pipeline
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    _p, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[],
                             selection={"install_intel_llvm": False, "oneapi": True})
    assert not ctx.selection.install_intel_llvm and ctx.selection.oneapi


def test_a_shipped_fragment_is_owned_by_the_name_in_its_filename():
    from pathlib import Path

    from sushihub.setup.dependency_source import _owner_for_shipped

    assert _owner_for_shipped(Path("manifests/gui.deps.toml")) == "gui"


def test_build_pipeline_honours_the_gpu_turned_off_in_customize(fake_cfg, bare_machine):
    from sushihub.setup.factory import build_pipeline
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    _p, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[],
                             selection={"gpu": False})
    assert not ctx.gpu


@pytest.mark.parametrize("step", ["verify", "all"])
def test_build_pipeline_knows_no_step_that_builds_a_module(fake_cfg, bare_machine, step):
    """The verify and all steps are gone from the names and refused by the factory."""
    from sushihub.setup.factory import STEP_NAMES, build_pipeline
    assert step not in STEP_NAMES
    with pytest.raises(ValueError):
        build_pipeline(only=step, cfg=fake_cfg, source=MemorySource([dep("cmake")]), managers=[])


def test_every_named_step_builds_a_pipeline(fake_cfg, bare_machine):
    """Each name in STEP_NAMES yields a pipeline."""
    from sushihub.setup.factory import STEP_NAMES, build_pipeline
    for step in STEP_NAMES:
        pipeline, _ctx = build_pipeline(only=step, cfg=fake_cfg,
                                        source=MemorySource([dep("cmake")]), managers=[])
        assert pipeline is not None
