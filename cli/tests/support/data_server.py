# data_server.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Serves fixed files from 127.0.0.1 and records every request, as a data package's publisher."""

from __future__ import annotations

import hashlib
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from sushihub.services.data import DataPackage


class RecordedRequest:
    """One request the server saw: its path and the User-Agent it carried."""

    def __init__(self, path: str, user_agent: str) -> None:
        """Hold the path and the client name."""
        self.path = path
        self.user_agent = user_agent


class ServedFiles:
    """A running server, the address it answers on and the requests it has seen."""

    def __init__(self, files: dict[str, bytes], port: int) -> None:
        """Hold the files to serve, keyed by URL path, and the bound port."""
        self.files = files
        self.port = port
        self.requests: list[RecordedRequest] = []

    def url(self, path: str) -> str:
        """Return the address of *path* on this server."""
        return f"http://127.0.0.1:{self.port}{path}"


@contextmanager
def serve(files: dict[str, bytes]) -> Iterator[ServedFiles]:
    """Serve *files* (URL path to bytes) on a free port until the block ends."""
    served = ServedFiles(files, 0)

    class Handler(BaseHTTPRequestHandler):
        """Answers a GET with the file of that path, or 404."""

        def do_GET(self) -> None:  # noqa: N802 - the name http.server dispatches on
            """Record the request and write the file."""
            served.requests.append(
                RecordedRequest(self.path, self.headers.get("User-Agent", "")))
            body = files.get(self.path)
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            """Print nothing."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    served.port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield served
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def package_of(served: ServedFiles, checkout: Path, path: str, *, destination: str,
               name: str = "reference", size: int | None = None, sha256: str | None = None,
               required: bool = False) -> DataPackage:
    """Return the package that pins the file served at *path*, with size or digest overridden."""
    body = served.files[path]
    return DataPackage(
        name=name, owner="astro", checkout=checkout, url=served.url(path),
        sha256=hashlib.sha256(body).hexdigest() if sha256 is None else sha256,
        size=len(body) if size is None else size, licence="public",
        destination=destination, required=required)
