# Wave 0: cover the five seams the decoupling rewrites

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin today's behaviour of the five seams that waves 1 through 4 rewrite, so each later
wave has something to answer to.

**Architecture:** Five test modules under `sushihub/cli/tests/`, one per seam, each importing
the module under test directly and monkeypatching its namespace. No test touches the network,
`dependencies/`, or a real pipx. The suite already carries `tests/conftest.py` with a
`MemorySource` fake and a `fake_cfg` fixture, and `tests/test_presence.py` carries a `Recorder`
that stands in for `console`; both are reused rather than re-created.

**Tech Stack:** Python 3.10+, pytest, `monkeypatch` and `tmp_path`.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §5 wave 0.

## Global Constraints

- These are characterization tests. They pass against today's code from the moment they are
  written. A failure means the assertion is wrong, not the code. The usual red-green cycle does
  not apply and no step below asks for a failing run.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`.
  Every test module opens with a one-line module docstring and every function carries a
  one-sentence docstring starting with its verb.
- No test opens a socket, runs git, runs pipx, or writes outside `tmp_path`.
- `tests/conftest.py` pins `SUSHISTACK_HOME` to the repository root before `sushistack` is
  imported. Any test that exercises workspace resolution must remove it with
  `monkeypatch.delenv("SUSHISTACK_HOME", raising=False)` first.
- The whole suite must still pass: `python -m pytest sushihub/cli/tests -q` reports 297 plus the
  tests this plan adds.
- Commit messages follow `commits`: `test(cli): <clause>`.

---

### Task 1: Workspace resolution

`sushistack.config` decides where the workspace, its config directory and its dependency tree
are. Wave 3 replaces all three answers, so today's answers are written down first.

**Files:**
- Test: `sushihub/cli/tests/test_workspace_resolution.py` (create)

**Interfaces:**
- Consumes: `sushistack.config.workspace_root`, `config_dir`, `deps_dir`, `WORKSPACE_MARKER`;
  `sushicore.workspace.WORKSPACE_CLI_DIR`.
- Produces: nothing later tasks read.

- [ ] **Step 1: Write the test module**

```python
"""Where `hub` decides the workspace, its config directory and its dependency tree are."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.workspace import WORKSPACE_CLI_DIR
from sushistack.config import (
    WORKSPACE_MARKER,
    config_dir,
    deps_dir,
    workspace_root,
)


@pytest.fixture
def unpinned(monkeypatch, tmp_path):
    """Drop the SUSHISTACK_HOME the suite's conftest pins and sit in an empty directory."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.delenv("SUSHISTACK_DEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_the_environment_variable_names_the_workspace(unpinned, monkeypatch, tmp_path):
    """SUSHISTACK_HOME wins over anything the current directory would say."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(elsewhere))
    assert workspace_root() == elsewhere.resolve()


def test_the_marker_is_found_by_walking_up(unpinned):
    """A .sushistack marker in an ancestor makes that ancestor the root."""
    (unpinned / WORKSPACE_MARKER).write_text("", encoding="utf-8")
    nested = unpinned / "sushiruntime" / "cli"
    nested.mkdir(parents=True)
    assert workspace_root(nested) == unpinned.resolve()


def test_the_manifests_tree_is_a_marker_of_its_own(unpinned):
    """The repository's own sushihub/cli/manifests signature marks a workspace."""
    (unpinned / WORKSPACE_CLI_DIR / "manifests").mkdir(parents=True)
    assert workspace_root(unpinned) == unpinned.resolve()


def test_no_marker_anywhere_exits(unpinned):
    """Resolution outside a workspace raises SystemExit naming the marker."""
    with pytest.raises(SystemExit) as caught:
        workspace_root(unpinned)
    assert WORKSPACE_MARKER in str(caught.value)


def test_the_config_directory_is_the_hub_cli_directory(unpinned):
    """config_dir resolves to <root>/sushihub/cli, inside the repository tree."""
    assert config_dir(unpinned) == unpinned / WORKSPACE_CLI_DIR
    assert config_dir(unpinned) == unpinned / Path("sushihub") / "cli"


def test_dependencies_default_to_one_tree_under_the_root(unpinned, monkeypatch):
    """deps_dir is <root>/dependencies when nothing overrides it."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(unpinned))
    assert deps_dir() == unpinned.resolve() / "dependencies"


def test_the_dependency_override_wins(unpinned, monkeypatch, tmp_path):
    """SUSHISTACK_DEPS_DIR replaces the tree under the root."""
    monkeypatch.setenv("SUSHISTACK_HOME", str(unpinned))
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(tmp_path / "elsewhere"))
    assert deps_dir() == tmp_path / "elsewhere"


def test_dependencies_fall_back_to_a_user_path_outside_a_workspace(unpinned, monkeypatch):
    """Outside a workspace deps_dir lands under a per-user SushiStack directory."""
    monkeypatch.setenv("LOCALAPPDATA", str(unpinned / "local"))
    assert deps_dir() == unpinned / "local" / "SushiStack" / "dependencies"
```

- [ ] **Step 2: Run the new module**

Run: `python -m pytest sushihub/cli/tests/test_workspace_resolution.py -v`
Expected: 8 passed.

- [ ] **Step 3: Run the whole suite**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 305 passed.

- [ ] **Step 4: Commit**

```bash
git add sushihub/cli/tests/test_workspace_resolution.py
git commit -m "test(cli): pin how the workspace, config and dependency paths resolve"
```

---

### Task 2: The module catalog

`MODULES`, `_ALIASES`, `_resolve_names` and `_GITIGNORE_LINES` are the catalog wave 2 moves into
`catalog.toml`. This task writes down what the catalog answers today, including the two modules
wave 2 removes.

**Files:**
- Test: `sushihub/cli/tests/test_catalog.py` (create)

**Interfaces:**
- Consumes: `sushistack.services.modules.MODULES`, `_ALIASES`, `_resolve_names`,
  `_GITIGNORE_LINES`, `BINARY_MODULE`, `SUSHICORE_NAME`;
  `sushihub/cli/tests/test_presence.Recorder`.
- Produces: nothing later tasks read.

- [ ] **Step 1: Write the test module**

```python
"""What the module catalog answers today: its members, their aliases and their expansion."""

from __future__ import annotations

import pytest

from sushistack.services import modules

from .test_presence import Recorder


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line the catalog prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_the_catalog_holds_the_six_modules_of_today():
    """Six modules are registered; wave 2 drops sushidsp and sushitrack from this list."""
    assert list(modules.MODULES) == [
        "sushiruntime",
        "sushiengine",
        "sushiai",
        "sushiblas",
        "sushidsp",
        "sushitrack",
    ]


def test_every_entry_names_its_repository_and_directory():
    """A catalog entry carries a github URL and a directory equal to its name."""
    for name, entry in modules.MODULES.items():
        assert entry.name == name
        assert entry.directory == name
        assert entry.repo == f"https://github.com/sushisystems/{name}.git"


def test_sushiengine_is_the_one_module_sold_as_a_binary():
    """BINARY_MODULE names sushiengine and nothing else."""
    assert modules.BINARY_MODULE == "sushiengine"
    assert modules.BINARY_MODULE in modules.MODULES


def test_sushicore_is_not_a_catalog_member():
    """sushicore ships inside the repository, so the catalog never lists it."""
    assert modules.SUSHICORE_NAME not in modules.MODULES


def test_every_module_has_a_two_letter_alias():
    """Each alias maps to a catalog member and no module is left without one."""
    assert set(modules._ALIASES.values()) == set(modules.MODULES)
    assert modules._ALIASES["sr"] == "sushiruntime"
    assert modules._ALIASES["se"] == "sushiengine"


def test_an_empty_list_means_every_module():
    """Passing nothing, or 'all', expands to the whole catalog in order."""
    assert modules._resolve_names(None) == list(modules.MODULES)
    assert modules._resolve_names([]) == list(modules.MODULES)
    assert modules._resolve_names(["all"]) == list(modules.MODULES)


def test_aliases_expand_to_module_names():
    """A list of aliases comes back as the names they stand for, in the order given."""
    assert modules._resolve_names(["se", "sr"]) == ["sushiengine", "sushiruntime"]


def test_a_name_outside_the_catalog_is_refused(recorder):
    """An unknown name returns None and the message names it and the choices."""
    assert modules._resolve_names(["sushiwater"]) is None
    assert recorder.said("sushiwater")
    assert recorder.said("sushiruntime")


def test_the_gitignore_lines_cover_every_module_and_the_local_files():
    """`hub init` ignores the dependency tree, every module directory and both local files."""
    lines = modules._GITIGNORE_LINES
    assert "/dependencies/" in lines
    for name in modules.MODULES:
        assert f"/{name}/" in lines
    assert "/sushihub/cli/config.local.toml" in lines
    assert "/sushihub/cli/modules.local.toml" in lines
```

- [ ] **Step 2: Run the new module**

Run: `python -m pytest sushihub/cli/tests/test_catalog.py -v`
Expected: 9 passed.

- [ ] **Step 3: Run the whole suite**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 314 passed.

- [ ] **Step 4: Commit**

```bash
git add sushihub/cli/tests/test_catalog.py
git commit -m "test(cli): pin the module catalog, its aliases and its expansion"
```

---

### Task 3: `hub init`

`modules.init` writes the marker file, appends to `.gitignore` and creates the dependency tree.
Wave 3 replaces the marker file with a directory, so every one of those effects is written down.

**Files:**
- Test: `sushihub/cli/tests/test_init.py` (create)

**Interfaces:**
- Consumes: `sushistack.services.modules.init`, `WORKSPACE_MARKER`, `_GITIGNORE_LINES`;
  `tests/test_presence.Recorder`.
- Produces: nothing later tasks read.

- [ ] **Step 1: Write the test module**

```python
"""What `hub init` leaves on disk: the marker, the .gitignore lines and the dependency tree."""

from __future__ import annotations

import pytest

from sushistack.config import WORKSPACE_MARKER
from sushistack.services import modules

from .test_presence import Recorder


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Run `hub init` in a throwaway directory whose dependency tree is also throwaway."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(modules, "deps_dir", lambda: tmp_path / "dependencies")
    return tmp_path


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line `hub init` prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_init_writes_the_marker_file(workspace, recorder):
    """The marker is a file whose comment says how to detach the directory."""
    assert modules.init() == 0
    marker = workspace / WORKSPACE_MARKER
    assert marker.is_file()
    assert "Delete it to detach this directory" in marker.read_text(encoding="utf-8")


def test_init_creates_the_dependency_tree(workspace, recorder):
    """The dependency directory exists afterwards, empty."""
    modules.init()
    assert (workspace / "dependencies").is_dir()


def test_init_writes_every_gitignore_line(workspace, recorder):
    """A fresh .gitignore carries each managed line exactly once."""
    modules.init()
    text = (workspace / ".gitignore").read_text(encoding="utf-8")
    for line in modules._GITIGNORE_LINES:
        assert text.count(line) == 1


def test_init_separates_its_lines_from_an_existing_file(workspace, recorder):
    """An existing .gitignore with no trailing newline keeps its last line intact."""
    (workspace / ".gitignore").write_text("build/", encoding="utf-8")
    modules.init()
    lines = (workspace / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "build/"
    assert "/dependencies/" in lines


def test_a_second_init_adds_nothing(workspace, recorder):
    """Running init twice leaves the .gitignore byte-identical and says so."""
    modules.init()
    first = (workspace / ".gitignore").read_text(encoding="utf-8")
    assert modules.init() == 0
    assert (workspace / ".gitignore").read_text(encoding="utf-8") == first
    assert recorder.said(f"Already a SushiStack workspace: {workspace.resolve()}")
```

- [ ] **Step 2: Run the new module**

Run: `python -m pytest sushihub/cli/tests/test_init.py -v`
Expected: 5 passed.

- [ ] **Step 3: Run the whole suite**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 319 passed.

- [ ] **Step 4: Commit**

```bash
git add sushihub/cli/tests/test_init.py
git commit -m "test(cli): pin what hub init writes into a fresh directory"
```

---

### Task 4: `hub link` and the link registry

`_write_link` writes `modules.local.toml` and `config.registered_modules` reads it. Wave 3 moves
that file into the workspace directory, so the round trip and the refusals are written down.

**Files:**
- Test: `sushihub/cli/tests/test_link.py` (create)

**Interfaces:**
- Consumes: `sushistack.services.modules.link`, `_write_link`, `MODULES_FILE`;
  `sushistack.config.registered_modules`; `sushicore.workspace.WORKSPACE_CLI_DIR`;
  `tests/test_presence.Recorder`.
- Produces: nothing later tasks read.

- [ ] **Step 1: Write the test module**

```python
"""What `hub link` records, where it records it, and which names it refuses."""

from __future__ import annotations

import pytest

from sushicore.workspace import WORKSPACE_CLI_DIR
from sushistack.config import MODULES_FILE, registered_modules
from sushistack.services import modules

from .test_presence import Recorder


@pytest.fixture
def cfg_dir(tmp_path, monkeypatch):
    """Point the link registry at a throwaway sushihub/cli directory."""
    target = tmp_path / WORKSPACE_CLI_DIR
    target.mkdir(parents=True)
    monkeypatch.setattr(modules, "config_dir", lambda: target)
    return target


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line `hub link` prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


def test_the_registry_file_carries_a_modules_table(cfg_dir, tmp_path):
    """_write_link writes a commented [modules] table naming the checkout."""
    modules._write_link("sushiruntime", tmp_path / "checkouts" / "sushiruntime")
    text = (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")
    assert "[modules]" in text
    assert "Managed by `hub link`" in text
    assert "sushiruntime" in text


def test_entries_are_written_in_name_order(cfg_dir, tmp_path):
    """Two links land sorted by module name, whatever order they were written in."""
    modules._write_link("sushiruntime", tmp_path / "a")
    modules._write_link("sushiai", tmp_path / "b")
    body = (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")
    assert body.index("sushiai") < body.index("sushiruntime")


def test_relinking_replaces_the_path_rather_than_repeating_it(cfg_dir, tmp_path):
    """Linking the same module twice leaves one entry, pointing at the newer path."""
    modules._write_link("sushiblas", tmp_path / "old")
    modules._write_link("sushiblas", tmp_path / "new")
    text = (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")
    assert text.count("sushiblas") == 1
    assert "new" in text


def test_the_registry_reads_back_what_link_wrote(cfg_dir, tmp_path, monkeypatch):
    """registered_modules returns the name-to-path map _write_link recorded."""
    checkout = tmp_path / "checkouts" / "sushiai"
    modules._write_link("sushiai", checkout)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    assert registered_modules() == {"sushiai": str(checkout)}


def test_link_refuses_sushicore(cfg_dir, recorder, tmp_path):
    """sushicore ships in the repository, so linking it is an error before any write."""
    assert modules.link("sushicore", str(tmp_path)) == 1
    assert recorder.said(
        "sushicore ships inside this repository and cannot be linked. Edit it in "
        "place, at `sushicore/`."
    )
    assert not (cfg_dir / MODULES_FILE).exists()


def test_link_refuses_a_name_outside_the_catalog(cfg_dir, recorder, tmp_path):
    """An unknown module is reported with the catalog's choices and nothing is written."""
    assert modules.link("sushiwater", str(tmp_path)) == 1
    assert recorder.said("Unknown module 'sushiwater'. Choose from: sushiruntime, "
                         "sushiengine, sushiai, sushiblas, sushidsp, sushitrack "
                         "(or their aliases: sr, se, sa, sb, sd, st).")
    assert not (cfg_dir / MODULES_FILE).exists()


def test_link_refuses_a_path_that_is_not_there(cfg_dir, recorder, tmp_path):
    """A missing directory is reported and nothing is written."""
    assert modules.link("sushiruntime", str(tmp_path / "nowhere")) == 1
    assert not (cfg_dir / MODULES_FILE).exists()


def test_link_takes_an_alias_and_records_the_full_name(cfg_dir, recorder, tmp_path):
    """`hub link sr <path>` records sushiruntime and skips provisioning when asked."""
    checkout = tmp_path / "sushiruntime"
    (checkout / ".git").mkdir(parents=True)
    assert modules.link("sr", str(checkout), skip_install=True,
                        provision=lambda dry: pytest.fail("provision ran")) == 0
    assert "sushiruntime" in (cfg_dir / MODULES_FILE).read_text(encoding="utf-8")


def test_a_dry_run_writes_nothing(cfg_dir, recorder, tmp_path):
    """A dry run reports the link it would make and leaves the registry absent."""
    checkout = tmp_path / "sushiblas"
    (checkout / ".git").mkdir(parents=True)
    assert modules.link("sushiblas", str(checkout), dry_run=True, skip_install=True) == 0
    assert not (cfg_dir / MODULES_FILE).exists()
    assert recorder.said(f"(dry-run) would link sushiblas -> {checkout.resolve()}")
```

- [ ] **Step 2: Run the new module**

Run: `python -m pytest sushihub/cli/tests/test_link.py -v`
Expected: 9 passed.

- [ ] **Step 3: Run the whole suite**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 328 passed.

- [ ] **Step 4: Commit**

```bash
git add sushihub/cli/tests/test_link.py
git commit -m "test(cli): pin the link registry's round trip and its refusals"
```

---

### Task 5: The `sushicore` injection

`_install_module_cli` pipx-installs a module's CLI and then injects `sushicore` from the fixed
path `<workspace>/sushicore`. Wave 1 deletes that injection, so its four outcomes are written
down first.

**Files:**
- Test: `sushihub/cli/tests/test_cli_install.py` (create)

**Interfaces:**
- Consumes: `sushistack.services.modules._install_module_cli`, `sushicore_dir`,
  `SUSHICORE_NAME`; `tests/test_presence.Recorder`.
- Produces: nothing later tasks read.

- [ ] **Step 1: Write the test module**

```python
"""How a module's own CLI is installed and where sushicore is injected from."""

from __future__ import annotations

import pytest

from sushistack.services import modules

from .test_presence import Recorder


class _Runs:
    """Stands in for subprocess.run and records each command with a fixed return code."""

    def __init__(self, code: int = 0) -> None:
        """Start with no recorded commands and the return code to report."""
        self.commands: list[list[str]] = []
        self._code = code

    def __call__(self, args, **kwargs):
        """Record one command and report the fixed return code."""
        self.commands.append(list(args))
        return type("Completed", (), {"returncode": self._code})()


@pytest.fixture
def recorder(monkeypatch):
    """Capture every line the CLI install prints."""
    spy = Recorder()
    monkeypatch.setattr(modules, "console", spy)
    return spy


@pytest.fixture
def checkout(tmp_path):
    """Build a module checkout carrying a cli/ package pipx could install."""
    cli = tmp_path / "sushiruntime" / "cli"
    cli.mkdir(parents=True)
    (cli / "pyproject.toml").write_text("", encoding="utf-8")
    return tmp_path / "sushiruntime"


@pytest.fixture
def root(tmp_path):
    """Build a workspace root carrying a sushicore distribution to inject."""
    core = tmp_path / modules.SUSHICORE_NAME
    core.mkdir()
    (core / "pyproject.toml").write_text("", encoding="utf-8")
    return tmp_path


def test_sushicore_is_found_at_a_fixed_path_under_the_root(root):
    """sushicore_dir resolves to <root>/sushicore when that carries a pyproject."""
    assert modules.sushicore_dir(root) == root / modules.SUSHICORE_NAME


def test_sushicore_is_none_when_the_checkout_is_partial(tmp_path):
    """A sushicore directory without a pyproject.toml counts as missing."""
    (tmp_path / modules.SUSHICORE_NAME).mkdir()
    assert modules.sushicore_dir(tmp_path) is None


def test_a_module_without_a_cli_package_is_skipped(tmp_path, recorder, root, monkeypatch):
    """A checkout carrying no cli/pyproject.toml succeeds without reaching for pipx."""
    monkeypatch.setattr(modules, "_pipx_cmd",
                        lambda: pytest.fail("pipx was looked for"))
    assert modules._install_module_cli("sushiai", tmp_path / "sushiai", root) is True
    assert recorder.said("sushiai: no cli/ package to install; skipping CLI install.")


def test_a_missing_pipx_is_a_warning(checkout, root, recorder, monkeypatch):
    """Without pipx the install reports failure and names the command to run later."""
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: None)
    assert modules._install_module_cli("sushiruntime", checkout, root) is False
    assert recorder.said("sushiruntime: pipx not found; skipping CLI install. Install "
                         f"it later with `pipx install {checkout / 'cli'}`.")


def test_a_missing_sushicore_stops_after_the_install(checkout, tmp_path, recorder,
                                                     monkeypatch):
    """pipx installs the CLI, then the absent sushicore is reported and nothing is injected."""
    runs = _Runs()
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: ["pipx"])
    monkeypatch.setattr(modules, "subprocess", type("S", (), {"run": runs}))
    assert modules._install_module_cli("sushiruntime", checkout, tmp_path) is False
    assert len(runs.commands) == 1
    assert runs.commands[0][:2] == ["pipx", "install"]
    assert recorder.said(f"sushiruntime: sushicore is missing from "
                         f"{tmp_path / modules.SUSHICORE_NAME}; the CLI may fail to "
                         "start. It ships with this repository -- `git checkout -- "
                         "sushicore` to restore it.")


def test_the_happy_path_installs_then_injects(checkout, root, recorder, monkeypatch):
    """pipx installs the module's cli/ and injects sushicore as an editable distribution."""
    runs = _Runs()
    monkeypatch.setattr(modules, "_pipx_cmd", lambda: ["pipx"])
    monkeypatch.setattr(modules, "subprocess", type("S", (), {"run": runs}))
    monkeypatch.setattr(modules, "_cli_package_name", lambda cli_dir, name: "sushiruntime-cli")
    assert modules._install_module_cli("sushiruntime", checkout, root) is True
    assert runs.commands[0] == ["pipx", "install", "--force", str(checkout / "cli")]
    assert runs.commands[1] == ["pipx", "inject", "sushiruntime-cli", "--editable",
                                str(root / modules.SUSHICORE_NAME)]
```

- [ ] **Step 2: Run the new module**

Run: `python -m pytest sushihub/cli/tests/test_cli_install.py -v`
Expected: 6 passed.

- [ ] **Step 3: Run the whole suite**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 334 passed.

- [ ] **Step 4: Update the backlog and the changelog**

In `docs/design/REMAINING_WORK.md`, change the decoupling programme's wave 0 row to read
`Landed 2026-09-21.` in place of its `Waits on` value, and delete the
**Five uncovered seams in `hub`** item from *Outside the programme*, whose work this task
finished.

In `docs/design/WORKSPACE_DECOUPLING.md`, change the wave 0 row's acceptance column to
`Landed 2026-09-21: 37 tests across five modules, suite at 334.`

Add one line to the top of the list in `docs/reference/CHANGELOG.md`:

```
- 2026-09-21 — Covered the workspace, catalog, init, link and sushicore-injection seams with 37 tests (`sushihub/cli/tests/`).
```

- [ ] **Step 5: Commit**

```bash
git add sushihub/cli/tests/test_cli_install.py docs/design/REMAINING_WORK.md docs/design/WORKSPACE_DECOUPLING.md docs/reference/CHANGELOG.md
git commit -m "test(cli): pin how a module's CLI is installed and sushicore injected"
```
