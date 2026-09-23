"""Re-export of :mod:`sushicore.provision.gpu.windows_installer`; the implementation
moved to sushicore. No hub code imports a name from here directly; the GPU
backends that used to (``cuda.py``) now reach it through sushicore instead.
"""

from __future__ import annotations
