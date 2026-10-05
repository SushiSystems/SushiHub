# Notices

SushiHub is Copyright (c) 2026 Sushi Systems and licensed under the PolyForm Noncommercial
License 1.0.0; see `LICENSE`. The material below keeps its own licence.

No third-party source is vendored in this repository, no file is ported from third-party code,
and no third-party binary or data set is tracked or redistributed. The tables list what
`hub install` and `pip` fetch onto the user's machine.

## Libraries the desktop application links

`hub install` fetches these into the untracked `dependencies/` tree from
`cli/sushihub/manifests/gui.deps.toml`, which names no version. The versions are the ones vcpkg
installed on 2026-10-05, and each licence was read from that port's `copyright` file.

| Component | Where | Source | Version | Licence |
| --- | --- | --- | --- | --- |
| Dear ImGui, GLFW and OpenGL3 backends | linked by `gui/src/` | https://github.com/ocornut/imgui | 1.92.8 | MIT, Copyright (c) 2014-2026 Omar Cornut; text in `third_party/licenses/imgui.txt` |
| GLFW | linked by `gui/src/` | https://github.com/glfw/glfw | 3.4 | zlib/libpng, Copyright (c) 2002-2006 Marcus Geelnard, 2006-2019 Camilla Löwy; text in `third_party/licenses/glfw3.txt` |
| JSON for Modern C++ | linked by `gui/src/` | https://github.com/nlohmann/json | 3.12.0 | MIT, Copyright (c) 2013-2025 Niels Lohmann; text in `third_party/licenses/nlohmann-json.txt` |
| GoogleTest | linked by `gui/tests/` only | https://github.com/google/googletest | 1.17.0 | BSD-3-Clause, Copyright 2008 Google Inc.; text in `third_party/licenses/gtest.txt` |

No build of the desktop application is distributed. One that is carries the four texts beside
the executable.

## Python packages `hub` depends on

`cli/pyproject.toml` declares these as ranges and `pip` resolves them at install time. Each
licence was read from the metadata of the distribution installed on 2026-10-05, whose version
is the one listed.

| Component | Where | Source | Declared | Read from | Licence |
| --- | --- | --- | --- | --- | --- |
| click | `cli/sushihub/` | https://github.com/pallets/click | `>=8.0` | 8.2.1 | BSD-3-Clause |
| typer | `cli/sushihub/` | https://github.com/fastapi/typer | `>=0.12` | 0.20.0 | MIT |
| rich | `cli/sushihub/` | https://github.com/Textualize/rich | `>=13.0` | 15.0.0 | MIT |
| keyring | `cli/sushihub/` | https://github.com/jaraco/keyring | `>=24` | 25.7.0 | MIT |
| tomli | `cli/sushihub/`, Python below 3.11 | https://github.com/hukkin/tomli | `>=2.0` | 2.4.0 | MIT |
| pytest | `cli/tests/`, test extra | https://github.com/pytest-dev/pytest | `>=7.0` | 9.1.1 | MIT |
| jsonschema | `cli/tests/`, test extra | https://github.com/python-jsonschema/jsonschema | `>=4.0` | 4.26.0 | MIT |
| setuptools | build backend | https://github.com/pypa/setuptools | `>=61.0` | 82.0.1 | MIT |
| sushicore | `cli/sushihub/` | https://github.com/SushiSystems/SushiCore | `>=0.7.0` | its repository | Sushi Systems' own; see that repository's `LICENSE` and `NOTICE.md` |

## Toolchains `hub install` provisions

The SYCL toolchains and GPU SDKs that `hub install` sets up (Intel oneAPI, CUDA, ROCm, Level
Zero) are downloaded from their vendors onto the user's machine by `sushicore` and fall under
the vendors' terms. This repository holds no copy of them.

## Earlier versions

sushihub 0.1.0, which is tag `v0.1.0` and the only release on PyPI, was published under the
Apache License 2.0 and stays available under it. So do the commits up to and including
`18de796`, the last one pushed to the public repository before the change; they include the
commit tagged `v0.2.0` (`2f36683`), which was never published to PyPI. The licence changes
with the commit that replaces `LICENSE`; each commit is under the `LICENSE` file in its own
tree.
