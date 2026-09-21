"""Ordering of dependency owners for reports that read top to bottom.

The shared build infrastructure comes first because every module stands on it,
and the modules follow in the order a build would need them: a module after the
modules it declares it builds on (``[module] depends_on``).
"""

from __future__ import annotations

from typing import Iterable

from .dependency_source import SHARED_OWNER, IDependencySource


def owner_order(source: IDependencySource, owners: Iterable[str]) -> list[str]:
    """Order owners: ``shared`` first, then modules in dependency order.

    Ties keep the input order. A ``depends_on`` entry naming an owner outside
    *owners* is ignored, so a partially cloned workspace still orders.

    @param source Reads each module's ``depends_on``; its ``all()`` is called
                  first because the TOML source fills that map there.
    @param owners The owner names to order, duplicates allowed.
    @return       Every distinct owner, ordered.
    @raise ValueError When the modules depend on one another in a cycle.
    """
    source.all()
    distinct = list(dict.fromkeys(owners))
    ordered = [o for o in distinct if o == SHARED_OWNER]
    pending = [o for o in distinct if o != SHARED_OWNER]
    known = set(pending)

    placed: set[str] = set()
    while pending:
        ready = next(
            (m for m in pending
             if all(u in placed for u in source.depends_on(m) if u in known)),
            None,
        )
        if ready is None:
            raise ValueError(
                "Modules depend on one another in a cycle: " + ", ".join(pending))
        pending.remove(ready)
        placed.add(ready)
        ordered.append(ready)
    return ordered
