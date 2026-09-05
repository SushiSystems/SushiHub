# Wave 1b: dependencies follow the modules — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** `ss install` provisions only what the present modules declare, `ss add` and `ss link`
provision what the module they bring needs, `ss doctor` reports dependencies by owner in
dependency order and calls an undeclared toolchain "not needed", and the install scripts stop
downloading toolchains into an empty workspace.

**Architecture:** One new module, `setup/selection.py`, derives the toolchain selection from the
aggregated manifests: a customizable component is on when a present module's fragment declares a
dependency of that name. `build_pipeline` takes the derived selection as its default instead of a
literal of four `True`s; `--customize` starts from the derived selection. A second new module,
`setup/ordering.py`, orders owners: `shared` first, then modules topologically by `[module]
depends_on`. `DetectStep` uses it for the inventory table and the readiness report. `ss add` and
`ss link` call the provision pipeline after they bring a module in.

**Tech Stack:** Python 3.10+, Typer, Rich, pytest.

**Spec:** `docs/agent/specs/2026-09-05-hub-design.md` §3 "Dependencies follow the present
modules" and §9 wave 1b.

## Global Constraints

- Touch only `cli/`, `install.sh`, `install.ps1`, `.github/workflows/ci.yml`, `cli/README.md`,
  `docs/getting_started/INSTALL.md`. Do not touch `sushicore/`; another agent is working there.
  Do not edit `docs/reference/CHANGELOG.md` or `docs/design/REMAINING_WORK.md`; report the lines.
- Do not edit `cli/sushistack/cli.py` outside the bodies of `add`, `link` and `install`, and do
  not add or rename a command. Wave 1a-cli owns the rest of that file.
- Do not start `cmake`, `ninja`, `ctest`, `ss install`, or any download. Tests use an in-memory
  `IDependencySource` and a fake `Config`; nothing touches the network or `dependencies/`.
- Every file, class and function carries a docstring in the shape `docs/CONTRIBUTING.md` sets.
  No separator comments, no history, no TODO. Existing separator comments in a file you edit may
  stay; do not add new ones.
- Commit per task, staging by path, never `git add -A`.

## File structure

| File | Responsibility |
|---|---|
| `cli/sushistack/setup/selection.py` (new) | `ToolchainSelection` and `selection_from_source`. Knows the four component names and which `InstallContext` field each gates, through `CUSTOMIZABLE_COMPONENTS`. |
| `cli/sushistack/setup/ordering.py` (new) | `owner_order(source, owners)`: `shared`, then modules in dependency order, stable for ties. |
| `cli/sushistack/setup/factory.py` | Default selection from `selection_from_source`. |
| `cli/sushistack/setup/steps.py` | `DetectStep`: rows grouped by owner in `owner_order`; a toolchain no present module declares reads "not needed"; readiness in the same order. |
| `cli/sushistack/services/customize.py` | Picker starts from the derived selection. |
| `cli/sushistack/services/setup.py` | The opening line names what will be installed from the selection, not a literal. |
| `cli/sushistack/services/modules.py` | `add` and `link` run provision after bringing a module in, unless `skip_install`. |
| `cli/sushistack/cli.py` | `add` and `link` gain `--skip-install`; `install` help text stops promising everything. Bodies only. |
| `install.sh`, `install.ps1` | Run `ss install` (base only now) and then `ss add` for requested modules; the next-step hint names `ss add`. |
| `cli/pyproject.toml` | `[project.optional-dependencies] test = ["pytest>=7.0"]`. |
| `cli/tests/` (new) | `__init__.py`, `conftest.py` with the in-memory source and fake config, `test_selection.py`, `test_ordering.py`, `test_detect_rows.py`, `test_add_provisions.py`. |
| `.github/workflows/ci.yml` | A `ss` job: install sushicore then `./cli[test]`, run `python -m pytest cli/tests -q`, same matrix as the `sushicore` job. |
| `cli/README.md`, `docs/getting_started/INSTALL.md` | Replace the two "today this is broken" paragraphs with the rule as it now holds. |

## The four components

`CUSTOMIZABLE_COMPONENTS` in `cli/sushistack/config.py` already pairs each component key with the
`InstallContext` field it gates: `intel-llvm → install_intel_llvm`, `adaptivecpp → install_acpp`,
`oneapi → oneapi`, `cuda → gpu`. The keys equal the dependency names sushiruntime's fragment
declares. That equality is the whole mechanism: a component is selected when `source.all()`
contains a `Dependency` named by that key whose `owner` is not `SHARED_OWNER`.

---

### Task 1: Test scaffolding for `cli/`

**Files:**
- Create: `cli/tests/__init__.py`, `cli/tests/conftest.py`
- Modify: `cli/pyproject.toml`

**Interfaces:**
- Produces, in `conftest.py`:
  ```python
  class MemorySource(IDependencySource):
      def __init__(self, deps: list[Dependency], depends_on: dict[str, list[str]] | None = None)
      def all(self) -> list[Dependency]
      def depends_on(self, module: str) -> list[str]

  def dep(name: str, owner: str = "shared", *, provides: str = "", required: bool = True,
          linux_apt=(), windows_vcpkg=(), check_cmd=()) -> Dependency

  @pytest.fixture
  def fake_cfg() -> Config   # Config(platform="linux") with every path field empty
  ```
  Look at `Config` and `ToolConfig` for the constructor; `ToolConfig` carries `platform`.

- [ ] **Step 1:** Write the two files. `MemorySource.all` returns the list as given; `depends_on`
reads the dict.
- [ ] **Step 2:** Add the `test` extra to `cli/pyproject.toml`.
- [ ] **Step 3:** From the repository root: `python -m pip install -e ./sushicore -e "./cli[test]"`
then `python -m pytest cli/tests -q`. Expected: "no tests ran", exit 5.
- [ ] **Step 4: Commit**

```bash
git add cli/tests/__init__.py cli/tests/conftest.py cli/pyproject.toml
git commit -m "test(cli): give ss a test scaffold with an in-memory dependency source"
```

---

### Task 2: `selection_from_source`

**Files:**
- Create: `cli/sushistack/setup/selection.py`
- Test: `cli/tests/test_selection.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class ToolchainSelection:
      install_intel_llvm: bool
      install_acpp: bool
      oneapi: bool
      gpu: bool
      def as_dict(self) -> dict[str, bool]          # field name -> value
      def components(self) -> list[str]             # selected component keys, in CUSTOMIZABLE_COMPONENTS order
      def merged(self, overrides: dict[str, bool]) -> "ToolchainSelection"   # unknown keys ignored

  def selection_from_source(source: IDependencySource) -> ToolchainSelection
      """On for each component a non-shared owner declares by name; off otherwise."""
  ```
- Consumes: `CUSTOMIZABLE_COMPONENTS`, `SHARED_OWNER`, `IDependencySource`.

- [ ] **Step 1: Write the failing tests**

```python
"""A toolchain is selected because a present module asked for it."""

from sushistack.setup.selection import ToolchainSelection, selection_from_source

from .conftest import MemorySource, dep


def test_empty_workspace_selects_no_toolchain():
    sel = selection_from_source(MemorySource([dep("cmake"), dep("ninja")]))
    assert sel == ToolchainSelection(False, False, False, False)


def test_runtime_fragment_turns_its_toolchains_on():
    src = MemorySource([dep("cmake"), dep("intel-llvm", "sushiruntime"), dep("cuda", "sushiruntime")])
    sel = selection_from_source(src)
    assert sel.install_intel_llvm and sel.gpu
    assert not sel.install_acpp and not sel.oneapi


def test_a_shared_fragment_cannot_select_a_toolchain():
    sel = selection_from_source(MemorySource([dep("intel-llvm", "shared")]))
    assert not sel.install_intel_llvm


def test_components_lists_selected_keys_in_catalogue_order():
    src = MemorySource([dep("oneapi", "sushiruntime"), dep("intel-llvm", "sushiruntime")])
    assert selection_from_source(src).components() == ["intel-llvm", "oneapi"]


def test_merged_applies_known_keys_only():
    sel = ToolchainSelection(False, False, False, False).merged({"gpu": True, "bogus": True})
    assert sel.gpu and sel.as_dict() == {"install_intel_llvm": False, "install_acpp": False,
                                         "oneapi": False, "gpu": True}
```

- [ ] **Step 2:** Run `python -m pytest cli/tests/test_selection.py -q`, confirm ImportError.
- [ ] **Step 3:** Implement. `components()` walks `CUSTOMIZABLE_COMPONENTS` and returns the key of
each whose field is true.
- [ ] **Step 4:** Run, confirm pass.
- [ ] **Step 5: Commit**

```bash
git add cli/sushistack/setup/selection.py cli/tests/test_selection.py
git commit -m "feat(cli): derive the toolchain selection from the present modules' fragments"
```

---

### Task 3: `build_pipeline` and the picker start from the derived selection

**Files:**
- Modify: `cli/sushistack/setup/factory.py`, `cli/sushistack/services/customize.py`,
  `cli/sushistack/services/setup.py`
- Test: `cli/tests/test_selection.py` (add)

**Interfaces:**
- `build_pipeline(..., selection: dict[str, bool] | None = None, ...)`: when `selection` is None
  the context is built from `selection_from_source(source)`; when given, from
  `selection_from_source(source).merged(selection)`. Signature unchanged.
- `customize.choose_components(defaults: dict[str, bool] | None = None)`: initial checks come from
  `defaults` (field name → bool) when given, else all True as today. `cli.py`'s `install` body
  passes `selection_from_source(TomlDependencySource()).as_dict()`.
- `services.setup.run`: the opening line becomes `f"Installing: {', '.join(names) or 'base tools only'}."`
  where `names` are `ToolchainSelection.components()` of the context. Build the message from
  `ctx` after `build_pipeline` returns; delete the "Installing everything" literal.

- [ ] **Step 1: Write the failing test**

```python
def test_build_pipeline_defaults_to_the_derived_selection(fake_cfg):
    from sushistack.setup.factory import build_pipeline
    src = MemorySource([dep("cmake"), dep("intel-llvm", "sushiruntime")])
    _pipeline, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[])
    assert ctx.install_intel_llvm and not ctx.install_acpp and not ctx.oneapi and not ctx.gpu


def test_build_pipeline_merges_an_explicit_selection_over_the_derived_one(fake_cfg):
    from sushistack.setup.factory import build_pipeline
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    _p, ctx = build_pipeline(only="detect", cfg=fake_cfg, source=src, managers=[],
                             selection={"install_intel_llvm": False, "oneapi": True})
    assert not ctx.install_intel_llvm and ctx.oneapi
```

- [ ] **Step 2:** Run, confirm the first fails (today every field is True).
- [ ] **Step 3:** Implement the three edits. In `cli.py`'s `install` body only: compute the
defaults and pass them to `choose_components`; change the docstring's second paragraph to "Installs
what the present modules declare. Use --customize to add or drop a toolchain."
- [ ] **Step 4:** `python -m pytest cli/tests -q`.
- [ ] **Step 5: Commit**

```bash
git add cli/sushistack/setup/factory.py cli/sushistack/services/customize.py cli/sushistack/services/setup.py cli/sushistack/cli.py cli/tests/test_selection.py
git commit -m "feat(cli): install what the present modules declare, and start the picker there"
```

---

### Task 4: `owner_order`

**Files:**
- Create: `cli/sushistack/setup/ordering.py`
- Test: `cli/tests/test_ordering.py`

**Interfaces:**
- Produces:
  ```python
  def owner_order(source: IDependencySource, owners: Iterable[str]) -> list[str]
      """`shared` first, then modules so that every module follows the ones it depends_on;
      ties keep the input order. A dependency cycle raises ValueError naming the modules."""
  ```
  Call `source.all()` before reading `depends_on` (the TOML source fills the map as a side effect
  of `all()`; the docstring on `TomlDependencySource.depends_on` says so).

- [ ] **Step 1: Write the failing tests**

```python
"""Owners are reported in the order a build would need them."""

import pytest

from sushistack.setup.ordering import owner_order

from .conftest import MemorySource, dep


def test_shared_comes_first_then_dependency_order():
    src = MemorySource([dep("a", "sushiai"), dep("b", "sushiblas"), dep("r", "sushiruntime")],
                       depends_on={"sushiai": ["sushiruntime", "sushiblas"], "sushiblas": ["sushiruntime"]})
    assert owner_order(src, ["sushiai", "shared", "sushiblas", "sushiruntime"]) == \
        ["shared", "sushiruntime", "sushiblas", "sushiai"]


def test_ties_keep_input_order():
    src = MemorySource([], depends_on={})
    assert owner_order(src, ["sushidsp", "sushiengine"]) == ["sushidsp", "sushiengine"]


def test_a_cycle_is_refused():
    src = MemorySource([], depends_on={"x": ["y"], "y": ["x"]})
    with pytest.raises(ValueError):
        owner_order(src, ["x", "y"])
```

- [ ] **Step 2:** Run, confirm ImportError. **Step 3:** Implement (Kahn's algorithm with a stable
queue). **Step 4:** Run. **Step 5: Commit**

```bash
git add cli/sushistack/setup/ordering.py cli/tests/test_ordering.py
git commit -m "feat(cli): order dependency owners the way a build needs them"
```

---

### Task 5: `DetectStep` reports by owner and says "not needed"

**Files:**
- Modify: `cli/sushistack/setup/steps.py` (`DetectStep` only)
- Test: `cli/tests/test_detect_rows.py`

**Interfaces:**
- Produces, on `DetectStep`:
  ```python
  def inventory_rows(self, ctx: InstallContext, all_deps: list[Dependency]) -> list[tuple[str, str, str, str]]
      """(component, status, owner, detail) rows, grouped by owner in owner_order; status is
      "OK", "MISSING" or "NOT NEEDED"."""
  ```
  `run` builds the table from `inventory_rows` (styling `OK` green, `MISSING` red, `NOT NEEDED`
  dim) and iterates the readiness report over `MODULES` filtered and ordered by `owner_order`.
  A toolchain row (`_add_toolchain_rows` today) is "NOT NEEDED" when no dependency in `all_deps`
  has that name with a non-shared owner; `ctx.detected[name]` is still recorded so readiness stays
  truthful. Extract the probing into `inventory_rows` so it is testable; `run` only prints.
  `probe.toolchain_status` and `probe.detect_gpu_vendor` touch the machine; take them as two
  injectable callables on `DetectStep.__init__` (`toolchain_status=probe.toolchain_status`,
  `gpu_vendor=probe.detect_gpu_vendor`) so tests pass stubs.

- [ ] **Step 1: Write the failing tests**

```python
"""What `ss doctor` says, and in what order."""

from sushistack.setup.pipeline import InstallContext
from sushistack.setup.steps import DetectStep

from .conftest import MemorySource, dep


def _step(src):
    return DetectStep(src, managers=[],
                      toolchain_status=lambda cfg, gpu: [("intel-llvm", False, ""), ("adaptivecpp", False, ""),
                                                         ("oneapi", False, ""), ("cuda", False, "")],
                      gpu_vendor=lambda: "none")


def test_undeclared_toolchains_are_not_needed(fake_cfg):
    src = MemorySource([dep("cmake")])
    rows = _step(src).inventory_rows(InstallContext(cfg=fake_cfg), src.all())
    status = {name: s for name, s, _o, _d in rows}
    assert status["intel-llvm"] == "NOT NEEDED" and status["cuda"] == "NOT NEEDED"


def test_declared_toolchains_are_missing_when_absent(fake_cfg):
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    rows = _step(src).inventory_rows(InstallContext(cfg=fake_cfg), src.all())
    assert dict((n, s) for n, s, _o, _d in rows)["intel-llvm"] == "MISSING"


def test_rows_are_grouped_by_owner_in_dependency_order(fake_cfg):
    src = MemorySource([dep("a", "sushiai"), dep("r", "sushiruntime"), dep("cmake")],
                       depends_on={"sushiai": ["sushiruntime"]})
    owners = [o for _n, _s, o, _d in _step(src).inventory_rows(InstallContext(cfg=fake_cfg), src.all())]
    first_index = {o: owners.index(o) for o in dict.fromkeys(owners)}
    assert first_index["shared"] < first_index["sushiruntime"] < first_index["sushiai"]
```

Rows for `python`, `git`, `cmake`, `ninja`, `pkg-config`, `doxygen` and "GPU vendor" belong to
`shared` unless a fragment names them. Keep the "SYCL compiler (active)" row under `sushiruntime`
only when sushiruntime is an owner in `all_deps`; otherwise omit it.

- [ ] **Step 2:** Run, confirm failure. **Step 3:** Implement. **Step 4:** Run all `cli/tests`.
- [ ] **Step 5: Commit**

```bash
git add cli/sushistack/setup/steps.py cli/tests/test_detect_rows.py
git commit -m "feat(cli): report dependencies by owner in build order, and name what is not needed"
```

---

### Task 6: `ss add` and `ss link` provision what they bring

**Files:**
- Modify: `cli/sushistack/services/modules.py` (`add`, `link`), `cli/sushistack/cli.py` (bodies of
  `add` and `link` only: a `skip_install: bool = typer.Option(False, "--skip-install", help="Do not run the dependency install afterwards.")`)
- Test: `cli/tests/test_add_provisions.py`

**Interfaces:**
- `modules.add(names, dry_run=False, skip_install=False, provision=None) -> int` and
  `modules.link(name, path, dry_run=False, skip_install=False, provision=None) -> int`.
  `provision` is a callable `(dry_run: bool) -> int`, defaulting to
  `lambda dry_run: setup_svc.run("provision", dry_run=dry_run)`; injected so tests never run the
  pipeline. It is called once, after the loop, when at least one module was newly cloned or newly
  linked (a module already present does not trigger it) and `skip_install` is False. With
  `dry_run`, it is called with `dry_run=True`. Its non-zero return becomes `add`'s return.
- `link`'s closing hint "Run `ss install` to pick up its dependencies." goes away when provision
  ran; stays when `--skip-install`.

- [ ] **Step 1: Write the failing tests**

```python
"""Bringing a module in brings its dependencies with it."""

from sushistack.services import modules


def test_add_provisions_once_after_a_new_clone(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(modules, "registered_modules", lambda: {})
    monkeypatch.setattr(modules, "_run_git", lambda args, cwd: (tmp_path / "sushiruntime" / ".git").mkdir(parents=True) or 0)
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    rc = modules.add(["sushiruntime"], provision=lambda dry_run: calls.append(dry_run) or 0)
    assert rc == 0 and calls == [False]


def test_add_skips_provision_when_nothing_new(monkeypatch, tmp_path):
    (tmp_path / "sushiruntime" / ".git").mkdir(parents=True)
    calls = []
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(modules, "registered_modules", lambda: {})
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    modules.add(["sushiruntime"], provision=lambda dry_run: calls.append(dry_run) or 0)
    assert calls == []


def test_add_honours_skip_install(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(modules, "registered_modules", lambda: {})
    monkeypatch.setattr(modules, "_run_git", lambda args, cwd: (tmp_path / "sushiruntime" / ".git").mkdir(parents=True) or 0)
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    modules.add(["sushiruntime"], skip_install=True, provision=lambda dry_run: calls.append(dry_run) or 0)
    assert calls == []
```

`modules.py` prints through `console`, which builds from the workspace config at import; if the
import fails outside a workspace under pytest, set `SUSHISTACK_HOME` to the repository root in
`conftest.py` (`os.environ.setdefault(...)`) and note it there.

- [ ] **Step 2:** Run, confirm failure. **Step 3:** Implement. **Step 4:** Run all `cli/tests`.
- [ ] **Step 5: Commit**

```bash
git add cli/sushistack/services/modules.py cli/sushistack/cli.py cli/tests/test_add_provisions.py
git commit -m "feat(cli): let ss add and ss link provision the dependencies they bring in"
```

---

### Task 7: The install scripts, CI, and the two manual pages

**Files:**
- Modify: `install.sh`, `install.ps1`, `.github/workflows/ci.yml`, `cli/README.md`,
  `docs/getting_started/INSTALL.md`

- [ ] **Step 1: Install scripts.** Keep `ss init` then `ss install` (it now installs the base
tools only). Then `ss add <modules>` when modules were requested; `ss add` provisions their
toolchains itself. Update both header comments: they no longer say "provisions everything (all SYCL
toolchains + CUDA)". The closing hint stays `Next: ss add sushiruntime`.
- [ ] **Step 2: CI.** Add a job `ss` beside `sushicore`, same matrix; steps: checkout, setup-python,
`pip install -e ./sushicore -e "./cli[test]"`, `python -m pytest cli/tests -q`.
- [ ] **Step 3: Docs.** In `cli/README.md` replace the paragraph starting "Today the toolchain
selection does not yet follow that rule" with two sentences: the selection is derived from the
present modules' fragments, and `ss add` / `ss link` provision what they bring unless
`--skip-install`. Add `--skip-install` to the `ss add` and `ss link` rows of the command table. In
`docs/getting_started/INSTALL.md` replace "What `ss install` downloads today" with "What `ss install`
downloads": the base tools in an empty workspace, each module's toolchains when it is added.
- [ ] **Step 4:** Verify by reading: `bash -n install.sh`; for the PowerShell script,
`powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw install.ps1)) | Out-Null"`.
Paste both outputs.
- [ ] **Step 5: Commit**

```bash
git add install.sh install.ps1 .github/workflows/ci.yml cli/README.md docs/getting_started/INSTALL.md
git commit -m "feat(install): provision the base tools first and let ss add bring the rest"
```

## Report

Paste: `python -m pytest cli/tests -q` after Task 7; `git log --oneline -7`; the two syntax
checks from Task 7; and these lines for the coordinator:

- CHANGELOG: `- 2026-09-05 — Derived the toolchain selection from the present modules and made `ss add` provision what it brings (`cli/sushistack/setup/selection.py`, `cli/sushistack/setup/factory.py`, `cli/sushistack/services/modules.py`).`
- CHANGELOG: `- 2026-09-05 — Ordered `ss doctor` by owner and marked undeclared toolchains not needed (`cli/sushistack/setup/ordering.py`, `cli/sushistack/setup/steps.py`).`
- REMAINING_WORK: wave 1b landed; "A test suite for `ss`" partly closed.
