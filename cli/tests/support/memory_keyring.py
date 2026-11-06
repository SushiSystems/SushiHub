# memory_keyring.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Provides an in-memory credential store, so a test never touches the OS keyring."""

from __future__ import annotations

import keyring.backend
import keyring.errors


class DictBackend(keyring.backend.KeyringBackend):
    """An in-memory credential store, so a test never touches the OS keyring."""

    priority = 1

    def __init__(self) -> None:
        """Start with no stored passwords."""
        super().__init__()
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        """Return the stored password, or None when there is none."""
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        """Store *password* under the service and username."""
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        """Forget the password stored under the service and username."""
        if (service, username) not in self.passwords:
            raise keyring.errors.PasswordDeleteError(username)
        del self.passwords[(service, username)]
