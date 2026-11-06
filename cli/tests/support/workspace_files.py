# workspace_files.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides the workspace roots a test points every `hub` lookup at."""

from __future__ import annotations

from pathlib import Path


def workspace_at(tmp_path: Path, monkeypatch) -> Path:
    """Point every `hub` lookup at *tmp_path* and return it as the workspace root."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    return tmp_path
