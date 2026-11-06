# contract_files.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides the JSON schemas of ``contract/`` to the tests that check a payload against one."""

from __future__ import annotations

import json
from pathlib import Path

K_CONTRACT = Path(__file__).resolve().parents[3] / "contract"


def contract_schema(name: str) -> dict:
    """Load the named schema from ``contract/``."""
    return json.loads((K_CONTRACT / name).read_text(encoding="utf-8"))
