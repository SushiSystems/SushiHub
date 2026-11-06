# fake_account_server.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides the fake Sushi Account server a test talks to over 127.0.0.1, and a client signed in to it."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from sushihub.services.identity import SushiAccount
from sushihub.services.token_store import MemoryStore, Tokens


class FakeIdState:
    """What the fake Sushi Account remembers between two requests."""

    def __init__(self) -> None:
        """Start with a grant nobody has approved yet and one licensed release."""
        self.approved = False
        self.denied = False
        self.expired = False
        self.slow_down_once = False
        self.polls = 0
        self.refreshes = 0
        self.refresh_ok = True
        self.bearers: list[str] = []
        self.licenses = [{"product": "sushiengine", "holder": "account",
                          "expires_at": "2027-03-01"},
                         {"product": "sushiai", "holder": "org", "expires_at": None}]
        self.products = {"sushiengine"}
        self.licensed = {"sushiengine"}
        self.licence_token = "licence-jwt"
        self.release_version = "1.4.2"      # None: the product has no release
        self.release_blob = b""             # what /download/<name> serves
        self.release_sha256: str | None = None   # None: the blob's own digest
        self.release_size: int | None = None     # None: the blob's own length
        self.rate_limited = False
        self.resolved: list[dict] = []      # every /api/releases/resolve body


def handler_for(state: FakeIdState):
    """Build a request handler answering the six endpoints out of *state*."""

    class Handler(BaseHTTPRequestHandler):
        """The six routes of contract/sushi-account.md, served from memory."""

        def log_message(self, fmt, *args):
            """Say nothing; the assertions are the test's output, not an access log."""

        def _reply(self, status: int, body: dict) -> None:
            """Write *body* as JSON under the given status."""
            blob = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)

        def _body(self) -> dict:
            """Read and parse the request body."""
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        def _bearer(self) -> bool:
            """Record the Authorization header and report whether it carries a token."""
            bearer = self.headers.get("Authorization", "")
            state.bearers.append(bearer)
            return bearer.startswith("Bearer ")

        def _licence_token(self, body: dict) -> None:
            """Answer the licence-token endpoint for the product *body* names."""
            product = body.get("product")
            if product not in state.products:
                self._reply(404, {"error": "unknown_product"})
            elif product not in state.licensed:
                self._reply(403, {"error": "no_licence"})
            else:
                self._reply(200, {"licence_token": state.licence_token,
                                  "expires_at": "2026-10-05T00:00:00Z"})

        def _resolve_release(self, body: dict) -> None:
            """Answer the release endpoint, pointing its url at this same server."""
            state.resolved.append(body)
            product = body.get("product")
            if state.rate_limited:
                self._reply(429, {"error": "rate_limited"})
            elif product not in state.products:
                self._reply(404, {"error": "unknown_product"})
            elif product not in state.licensed:
                self._reply(403, {"error": "no_licence"})
            elif state.release_version is None:
                self._reply(404, {"error": "no_release"})
            else:
                digest = hashlib.sha256(state.release_blob).hexdigest()
                self._reply(200, {
                    "version": state.release_version,
                    "platform": body.get("platform"),
                    "url": f"http://{self.headers.get('Host')}/download/{product}.zip",
                    "sha256": state.release_sha256 or digest,
                    "size": (len(state.release_blob) if state.release_size is None
                             else state.release_size),
                    "expires_at": "2026-09-05T00:10:00Z"})

        def do_POST(self):
            """Answer the device, refresh, licence-token and release endpoints."""
            body = self._body()
            if self.path in ("/api/licenses/token", "/api/releases/resolve"):
                if not self._bearer():
                    self._reply(401, {"error": "unauthorized"})
                elif self.path == "/api/licenses/token":
                    self._licence_token(body)
                else:
                    self._resolve_release(body)
            elif self.path == "/api/device/code":
                self._reply(200, {"device_code": "dev-1", "user_code": "WXYZ-1234",
                                  "verification_uri": "http://127.0.0.1/activate",
                                  "expires_in": 600, "interval": 1})
            elif self.path == "/api/device/token":
                state.polls += 1
                if state.denied:
                    self._reply(400, {"error": "access_denied"})
                elif state.expired:
                    self._reply(400, {"error": "expired_token"})
                elif state.slow_down_once and state.polls == 1:
                    self._reply(400, {"error": "slow_down"})
                elif state.approved:
                    self._reply(200, {"access_token": "access-1",
                                      "refresh_token": "refresh-1", "expires_in": 3600})
                else:
                    self._reply(400, {"error": "authorization_pending"})
            elif self.path == "/api/token/refresh":
                state.refreshes += 1
                if state.refresh_ok and body.get("refresh_token"):
                    self._reply(200, {"access_token": "access-2", "expires_in": 3600})
                else:
                    self._reply(401, {"error": "invalid_grant"})
            else:
                self._reply(404, {})

        def do_GET(self):
            """Answer the account endpoint, and serve the release the resolver named."""
            if self.path.startswith("/download/"):
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(state.release_blob)))
                self.end_headers()
                self.wfile.write(state.release_blob)
                return
            bearer = self.headers.get("Authorization", "")
            state.bearers.append(bearer)
            if self.path != "/api/me" or not bearer.startswith("Bearer "):
                self._reply(401, {})
                return
            self._reply(200, {"account_id": "acc-1", "email": "dev@sushisystems.io",
                              "licenses": state.licenses})

    return Handler


@contextmanager
def serve() -> Iterator[SimpleNamespace]:
    """Serve the endpoints from a thread on 127.0.0.1 and stop it afterwards.

    Yields:
        The server's ``url`` and the :class:`FakeIdState` it answers out of.
    """
    state = FakeIdState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state))
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01},
                              daemon=True)
    thread.start()
    try:
        yield SimpleNamespace(url=f"http://127.0.0.1:{server.server_address[1]}", state=state)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def signed_in(fake_id) -> SushiAccount:
    """Build a client whose store already holds a live session."""
    return SushiAccount(fake_id.url, MemoryStore(Tokens("access-1", "refresh-1", 1e12)),
                   now=lambda: 0.0)
