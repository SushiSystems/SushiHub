# sudo_prompt.py
# SushiHub - https://github.com/SushiSystems/SushiHub
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Asks for the sudo password once, while its prompt still owns the terminal."""

from __future__ import annotations

import os
import shutil
import sys

from sushicore.proc import Runner
from sushicore.provision.system import is_root
from sushicore.quiet_console import QuietConsole

from .. import console

#: The terminal a prompt reads from when stdin is not one.
K_TTY = "/dev/tty"

#: The text sudo prints before it reads the password.
K_SUDO_PROMPT = "[sudo] password for %p: "


def prime_sudo() -> None:
    """Prompt for the sudo password once, before any progress display starts.

    Nothing happens on Windows, for the superuser, or where sudo is not installed. Without a
    terminal the prompt is skipped and a warning names the way to authorize sudo beforehand.
    """
    if os.name == "nt" or is_root() or shutil.which("sudo") is None:
        return
    tty = None
    if not (sys.stdin and sys.stdin.isatty()):
        try:
            tty = open(K_TTY, "r", encoding="utf-8")
        except OSError:
            console.warn(
                "No terminal available for a sudo password prompt. If dependency "
                "installation fails, run the install command directly in a terminal, "
                "or pre-authorize with `sudo -v`."
            )
            return
    console.warn("Administrator (sudo) access needed — enter your password below.")
    try:
        Runner(QuietConsole(), "sushihub").run(["sudo", "-p", K_SUDO_PROMPT, "-v"], None, stdin=tty)
    finally:
        if tty is not None:
            tty.close()
