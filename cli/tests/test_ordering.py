"""Owners are reported in the order a build would need them."""

import pytest

from sushihub.setup.ordering import owner_order

from .conftest import MemorySource, dep


def test_shared_comes_first_then_dependency_order():
    src = MemorySource([dep("a", "sushiai"), dep("b", "sushiblas"), dep("r", "sushiruntime")],
                       depends_on={"sushiai": ["sushiruntime", "sushiblas"], "sushiblas": ["sushiruntime"]})
    assert owner_order(src, ["sushiai", "shared", "sushiblas", "sushiruntime"]) == \
        ["shared", "sushiruntime", "sushiblas", "sushiai"]


def test_ties_keep_input_order():
    src = MemorySource([], depends_on={})
    assert owner_order(src, ["sushidsp", "sushiengine"]) == ["sushidsp", "sushiengine"]


def test_a_cycle_is_refused():
    src = MemorySource([], depends_on={"x": ["y"], "y": ["x"]})
    with pytest.raises(ValueError):
        owner_order(src, ["x", "y"])
