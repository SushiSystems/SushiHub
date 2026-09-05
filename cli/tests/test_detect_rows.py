"""What `ss doctor` says, and in what order."""

from sushistack.setup.pipeline import InstallContext
from sushistack.setup.steps import DetectStep

from .conftest import MemorySource, dep


def _step(src):
    return DetectStep(src, managers=[],
                      toolchain_status=lambda cfg, gpu: [("intel-llvm", False, ""), ("adaptivecpp", False, ""),
                                                         ("oneapi", False, ""), ("cuda", False, "")],
                      gpu_vendor=lambda: "none")


def test_undeclared_toolchains_are_not_needed(fake_cfg):
    src = MemorySource([dep("cmake")])
    rows = _step(src).inventory_rows(InstallContext(cfg=fake_cfg), src.all())
    status = {name: s for name, s, _o, _d in rows}
    assert status["intel-llvm"] == "NOT NEEDED" and status["cuda"] == "NOT NEEDED"


def test_declared_toolchains_are_missing_when_absent(fake_cfg):
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    rows = _step(src).inventory_rows(InstallContext(cfg=fake_cfg), src.all())
    assert dict((n, s) for n, s, _o, _d in rows)["intel-llvm"] == "MISSING"


def test_rows_are_grouped_by_owner_in_dependency_order(fake_cfg):
    src = MemorySource([dep("a", "sushiai"), dep("r", "sushiruntime"), dep("cmake")],
                       depends_on={"sushiai": ["sushiruntime"]})
    owners = [o for _n, _s, o, _d in _step(src).inventory_rows(InstallContext(cfg=fake_cfg), src.all())]
    first_index = {o: owners.index(o) for o in dict.fromkeys(owners)}
    assert first_index["shared"] < first_index["sushiruntime"] < first_index["sushiai"]
