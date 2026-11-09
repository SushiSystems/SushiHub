# test_data_step.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The data step of `hub install`, the flag that skips it, and where its packages come from."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from sushihub import cli
from sushihub.services.data import (
    DataFragmentError,
    DataInstaller,
    DataPlacer,
    DataStore,
    HttpDownloader,
    WorkspaceDataSource,
)
from sushihub.setup import InstallContext, StepResult
from sushihub.setup.data_step import DataStep
from sushihub.setup.factory import build_pipeline

from .conftest import MemorySource, dep
from .support.data_server import package_of, serve
from .support.listed_packages import ListedPackages, RefusedFragment

pytestmark = pytest.mark.medium

K_BODY = b"gravity coefficients " * 32
K_PATH = "/egm2008.gz"
K_FRAGMENT = """
[data.egm]
url         = "http://127.0.0.1:9/egm2008.gz"
sha256      = "{digest}"
bytes       = 10
licence     = "MIT"
destination = "assets/egm2008.gz"
"""


def _step(tmp_path, out, *packages) -> DataStep:
    """Return a data step over *packages* with its store under *tmp_path*."""
    placer = DataPlacer()
    installer = DataInstaller(DataStore(tmp_path / "data", HttpDownloader()), placer, out)
    return DataStep(ListedPackages(*packages), installer, placer, out)


def _module(workspace, fragment_text: str):
    """Create the cloned sushiruntime module with *fragment_text* as its fragment."""
    module = workspace / "sushiruntime"
    (module / "cli").mkdir(parents=True)
    (module / "cli" / "sushistack.deps.toml").write_text(fragment_text, encoding="utf-8")
    (module / ".git").mkdir()
    return module


def test_data_source_lists_the_packages_of_a_cloned_module_with_its_checkout(workspace):
    module = _module(workspace, K_FRAGMENT.format(digest="a" * 64))
    packages = WorkspaceDataSource(workspace).packages()
    assert [(p.name, p.owner, p.checkout) for p in packages] == [("egm", "sushiruntime", module)]


def test_data_source_ignores_a_module_that_is_not_cloned(workspace):
    module = _module(workspace, K_FRAGMENT.format(digest="a" * 64))
    (module / ".git").rmdir()
    assert WorkspaceDataSource(workspace).packages() == []


def test_data_source_refuses_a_module_whose_table_lacks_a_field(workspace):
    _module(workspace, "[data.egm]\nurl = \"http://127.0.0.1/x\"\n")
    with pytest.raises(DataFragmentError, match="no 'sha256'"):
        WorkspaceDataSource(workspace).packages()


def test_step_installs_each_package(tmp_path, out, fake_cfg):
    checkout = tmp_path / "module"
    checkout.mkdir()
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, checkout, K_PATH, destination="egm.gz")
        result = _step(tmp_path, out, package).run(InstallContext(cfg=fake_cfg))
    assert result is StepResult.OK
    assert (checkout / "egm.gz").read_bytes() == K_BODY


def test_step_is_skipped_when_no_module_declares_a_package(tmp_path, out, fake_cfg):
    assert _step(tmp_path, out).run(InstallContext(cfg=fake_cfg)) is StepResult.SKIPPED


def test_step_fails_when_a_required_package_fails(tmp_path, out, fake_cfg):
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="egm.gz",
                             sha256="2" * 64, required=True)
        result = _step(tmp_path, out, package).run(InstallContext(cfg=fake_cfg))
    assert result is StepResult.FAILED


def test_step_records_a_warning_when_an_optional_package_fails(tmp_path, out, fake_cfg):
    ctx = InstallContext(cfg=fake_cfg)
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="egm.gz", sha256="2" * 64)
        result = _step(tmp_path, out, package).run(ctx)
    assert result is StepResult.OK
    assert len(ctx.warnings) == 1 and "sha256 expected " + "2" * 64 in ctx.warnings[0]


def test_step_fails_when_a_fragment_declares_a_table_wrongly(tmp_path, out, fake_cfg):
    placer = DataPlacer()
    installer = DataInstaller(DataStore(tmp_path / "data", HttpDownloader()), placer, out)
    step = DataStep(RefusedFragment(DataFragmentError("fragment: [data.x] has no 'url'")),
                    installer, placer, out)
    assert step.run(InstallContext(cfg=fake_cfg)) is StepResult.FAILED
    assert out.texts("error") == ["fragment: [data.x] has no 'url'"]


def test_step_under_a_dry_run_makes_no_request_and_writes_nothing(tmp_path, out, fake_cfg):
    with serve({K_PATH: K_BODY}) as served:
        package = package_of(served, tmp_path, K_PATH, destination="egm.gz")
        result = _step(tmp_path, out, package).run(InstallContext(cfg=fake_cfg, dry_run=True))
    assert result is StepResult.OK
    assert served.requests == []
    assert not (tmp_path / "egm.gz").exists() and not (tmp_path / "data").exists()


def test_pipeline_ends_with_the_data_step(fake_cfg, workspace):
    pipeline, _ = build_pipeline(cfg=fake_cfg, source=MemorySource([dep("cmake")]), managers=[],
                                 data_source=ListedPackages())
    assert [step.name for step in pipeline.steps][-1] == "data"


def test_pipeline_leaves_the_data_step_out_without_data(fake_cfg, workspace):
    pipeline, _ = build_pipeline(cfg=fake_cfg, source=MemorySource([dep("cmake")]), managers=[],
                                 data=False, data_source=ListedPackages())
    assert "data" not in [step.name for step in pipeline.steps]


def test_install_no_data_asks_the_service_to_skip_data(monkeypatch):
    seen: dict[str, object] = {}
    monkeypatch.setattr(cli.setup_svc, "run", lambda *args, **kwargs: seen.update(kwargs) or 0)
    CliRunner().invoke(cli.app, ["install", "--no-data"])
    assert seen["with_data"] is False


def test_install_without_the_flag_asks_the_service_for_data(monkeypatch):
    seen: dict[str, object] = {}
    monkeypatch.setattr(cli.setup_svc, "run", lambda *args, **kwargs: seen.update(kwargs) or 0)
    CliRunner().invoke(cli.app, ["install"])
    assert seen["with_data"] is True
