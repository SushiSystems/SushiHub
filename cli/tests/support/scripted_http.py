# scripted_http.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides the scripted http seam of a Sushi Account client and a client built over it."""

from __future__ import annotations

import json
import urllib.request

from sushihub.services.identity import SushiAccount
from sushihub.services.token_store import MemoryStore, Tokens


class Reply:
    """An open response of a given status whose body is JSON, as urlopen returns one."""

    def __init__(self, status: int, body: dict) -> None:
        """Hold the status and the JSON body to answer with."""
        self.status = status
        self._payload = json.dumps(body).encode("utf-8")

    def __enter__(self) -> "Reply":
        """Return the response itself, as urlopen's does."""
        return self

    def __exit__(self, *exc) -> None:
        """Close nothing."""

    def read(self) -> bytes:
        """Return the whole body."""
        return self._payload


class ScriptedHttp:
    """The http seam of a client: answers from a script and keeps every request it saw."""

    def __init__(self, *replies: Reply) -> None:
        """Answer the requests with *replies*, in order."""
        self._replies = list(replies)
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request, timeout):
        """Record *request* and return the next scripted reply."""
        self.requests.append(request)
        return self._replies.pop(0)


def signed_in_over(http) -> SushiAccount:
    """Return a client with a live session whose requests go through *http*."""
    return SushiAccount("http://account.invalid",
                        MemoryStore(Tokens("access-1", "refresh-1", 1e12)),
                        http=http, now=lambda: 0.0)
