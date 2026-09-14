"""GPU backend provisioning: one brick per vendor, one branch per platform.

Callers reach a backend through :mod:`registry`, never through this package's
namespace, so nothing is re-exported here.
"""

from __future__ import annotations
