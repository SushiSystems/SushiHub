# windows_installer.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Re-export of :mod:`sushicore.provision.gpu.windows_installer`; the implementation
moved to sushicore. No hub code imports a name from here directly; the GPU
backends that used to (``cuda.py``) now reach it through sushicore instead.
"""

from __future__ import annotations
