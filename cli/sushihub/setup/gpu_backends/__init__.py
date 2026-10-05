# __init__.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""GPU backend provisioning: one brick per vendor, one branch per platform.

Callers reach a backend through :mod:`registry`, never through this package's
namespace, so nothing is re-exported here.
"""

from __future__ import annotations
