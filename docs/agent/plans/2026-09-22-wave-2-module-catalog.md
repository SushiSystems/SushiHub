# Wave 2: the module catalog leaves the code

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the six hard-coded modules out of `services/modules.py` into a `catalog.toml` that
ships inside the `sushihub` distribution, read through one interface, and then take `sushidsp`
and `sushitrack` out of the stack.

**Architecture:** One brick, `ModuleCatalog`, owns what the stack contains. Its data is a TOML
file in the package; its three readers (`services/modules.py`, `services/status_report.py`,
`setup/steps.py`) go through the interface rather than a dict. The wave lands in four steps that
each leave the suite green: introduce the catalog with today's six entries and no behaviour
change, fold `BINARY_MODULE` into an entry field, remove the two modules, then correct a refusal
message wave 1 left false.

**Tech Stack:** Python 3.10+, `tomllib`, `importlib.resources`, setuptools package data, pytest.

**Spec:** `docs/design/WORKSPACE_DECOUPLING.md`, §3.1 and §5 wave 2.

## Global Constraints

- Task 3 is a breaking change to `hub add`, `hub link`, `hub install-cli` and `hub update`: three
  of them stop accepting `sushidsp`, `sushitrack`, `sd` and `st`. Its commit carries `!`.
  `api-stability` and `versioning-and-release` govern it.
- `catalog.toml` is a persistent file format read by a released tool. `file-formats` governs its
  shape, and the shape is fixed in task 1 rather than grown later.
- The catalog stays closed: it lists Sushi modules and no mechanism reads a catalog from
  anywhere else. The seam that would allow it is the point, not a feature to build now.
- Every task ends with `python -m pytest sushihub/cli/tests -q` green and states its count.
- Python style follows `python-code-style`; comments and docstrings follow `source-comments`;
  commit messages follow `commits`.
- Do not touch `sushicore_dir` or `_sushicore_row`. The owner deferred the `hub status`
  `sushicore` row to wave 5 on 2026-09-22; it reports `missing` until then, by decision.

## What this wave rewrites from wave 0

`sushihub/cli/tests/test_catalog.py` pins today's catalog: it asserts the six names in order,
that every entry's `repo` is a github URL and its `directory` equals its name, that
`BINARY_MODULE` is `sushiengine`, and that `_GITIGNORE_LINES` carries a line per module. Every
one of those assertions is about to change or move behind the new interface. Rewriting them is
the work, not an obstacle: they are what makes each change visible.

`sushihub/cli/tests/test_link.py` pins the refusal messages, including the exact sentence task 4
corrects and the exact list of names task 3 shortens.

---

### Task 1: ModuleCatalog, with today's six entries

A pure refactor. Behaviour is identical at the end of it: same six modules, same aliases, same
messages. Only the shape changes, so that tasks 2 and 3 have one place to edit.

**Files:**
- Create: `sushihub/cli/sushistack/services/catalog.py`
- Create: `sushihub/cli/sushistack/catalog.toml`
- Modify: `sushihub/cli/pyproject.toml`
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/sushistack/services/status_report.py`
- Modify: `sushihub/cli/sushistack/setup/steps.py`
- Modify: `sushihub/cli/tests/test_catalog.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `sushistack.services.catalog` exporting `Module`, `ModuleCatalog` and `CATALOG`.
  `Module` carries `name: str`, `repo: str`, `directory: str`, `alias: str` and
  `distribution: str`. `ModuleCatalog` exposes `names() -> list[str]`,
  `aliases() -> dict[str, str]`, `resolve(name: str) -> str | None`,
  `__contains__`, `__getitem__` and `__iter__`. `CATALOG` is the module-level instance loaded
  from the packaged `catalog.toml`.

- [ ] **Step 1: Write the catalog data**

`sushihub/cli/sushistack/catalog.toml`. The values are today's, copied from
`services/modules.py:48` and `:78`, with `distribution` carrying what `BINARY_MODULE` says
today. Order matters: it is the order `hub add all` and `hub status` use.

```toml
# The modules `hub` can bring into a workspace, in the order every command lists them.
#
# Each table's key is the module's name on the command line and the directory `hub add`
# clones into; the two are deliberately the same, because every module's own cmake resolves a
# sibling checkout by that flat <workspace>/<module> layout.
#
# Fields:
#   repo          git clone URL.
#   directory     directory created under the workspace root.
#   alias         the module's own CLI program name, accepted wherever a name is.
#   distribution  "source" to clone, "binary" for the one module sold as a compiled release.

[sushiruntime]
repo = "https://github.com/sushisystems/sushiruntime.git"
directory = "sushiruntime"
alias = "sr"
distribution = "source"

[sushiengine]
repo = "https://github.com/sushisystems/sushiengine.git"
directory = "sushiengine"
alias = "se"
distribution = "binary"

[sushiai]
repo = "https://github.com/sushisystems/sushiai.git"
directory = "sushiai"
alias = "sa"
distribution = "source"

[sushiblas]
repo = "https://github.com/sushisystems/sushiblas.git"
directory = "sushiblas"
alias = "sb"
distribution = "source"

[sushidsp]
repo = "https://github.com/sushisystems/sushidsp.git"
directory = "sushidsp"
alias = "sd"
distribution = "source"

[sushitrack]
repo = "https://github.com/sushisystems/sushitrack.git"
directory = "sushitrack"
alias = "st"
distribution = "source"
```

- [ ] **Step 2: Write the brick**

`sushihub/cli/sushistack/services/catalog.py`:

```python
"""What the stack contains, read from the catalog that ships with this package.

The catalog is data rather than code so that adding a module is an edit to
``catalog.toml`` and nothing else, and so that a later change of source -- a
catalog fetched from a server, a module that describes itself -- replaces one
loader instead of every reader.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Iterator

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


CATALOG_FILE = "catalog.toml"


@dataclass(frozen=True)
class Module:
    """One stack module: how to fetch it, where it lands, and what it is called."""

    name: str
    repo: str
    directory: str
    alias: str
    distribution: str

    @property
    def is_binary(self) -> bool:
        """Report whether this module ships as a compiled release rather than a clone."""
        return self.distribution == "binary"


class ModuleCatalog:
    """The modules `hub` knows, indexed by name and by alias."""

    def __init__(self, entries: dict[str, Module]) -> None:
        """Store the entries in the order given and index their aliases."""
        self._entries = dict(entries)
        self._aliases = {m.alias: m.name for m in self._entries.values()}

    def names(self) -> list[str]:
        """Return every module name, in catalog order."""
        return list(self._entries)

    def aliases(self) -> dict[str, str]:
        """Return the alias-to-name map."""
        return dict(self._aliases)

    def resolve(self, name: str) -> str | None:
        """Return the module name *name* stands for, or None when it names nothing."""
        resolved = self._aliases.get(name, name)
        return resolved if resolved in self._entries else None

    def __contains__(self, name: str) -> bool:
        """Report whether *name* is a module name in this catalog."""
        return name in self._entries

    def __getitem__(self, name: str) -> Module:
        """Return the entry for *name*."""
        return self._entries[name]

    def __iter__(self) -> Iterator[str]:
        """Iterate module names in catalog order."""
        return iter(self._entries)


def load_catalog() -> ModuleCatalog:
    """Build the catalog from the ``catalog.toml`` shipped inside this package.

    @pre The file is package data; a source checkout and an installed wheel both
        resolve it through ``importlib.resources``.
    """
    raw = (files("sushistack") / CATALOG_FILE).read_text(encoding="utf-8")
    doc = tomllib.loads(raw)
    entries = {
        name: Module(name=name, repo=body["repo"], directory=body["directory"],
                     alias=body["alias"], distribution=body["distribution"])
        for name, body in doc.items()
    }
    return ModuleCatalog(entries)


CATALOG = load_catalog()
```

- [ ] **Step 3: Ship the file in the wheel**

In `sushihub/cli/pyproject.toml`, the package-data entry today reads
`sushistack = ["py.typed"]`. Change it to:

```toml
sushistack = ["py.typed", "catalog.toml"]
```

Without this the file is missing from an installed wheel and `load_catalog` raises at import.

- [ ] **Step 4: Point the three readers at the catalog**

In `services/modules.py`:

- Delete the `Module` dataclass, the `MODULES` dict and `_ALIASES`, and import
  `from .catalog import CATALOG`. Add `Module` to that import only if a type annotation in this
  file still names it; an unused import is a lint failure, not a courtesy.
- `_GITIGNORE_LINES` builds its module lines from `CATALOG`: replace
  `*(f"/{m.directory}/" for m in MODULES.values())` with
  `*(f"/{CATALOG[n].directory}/" for n in CATALOG)`.
- `module_dest` reads `CATALOG[name].directory`.
- `_resolve_names` uses `CATALOG.resolve` rather than `_ALIASES.get` plus a membership test:

```python
def _resolve_names(names: list[str] | None) -> list[str] | None:
    """Expand a user module list ('all' or names) to concrete module names.

    Returns None on an unknown name (after reporting it), so callers can abort.
    """
    if not names or names == ["all"]:
        return CATALOG.names()
    resolved = [(n, CATALOG.resolve(n)) for n in names]
    unknown = [given for given, found in resolved if found is None]
    if unknown:
        console.error(f"Unknown module(s): {', '.join(unknown)}. "
                      f"Choose from: {', '.join(CATALOG.names())} (or their aliases: "
                      f"{', '.join(CATALOG.aliases())}; or 'all').")
        return None
    return [found for _, found in resolved]
```

  Note the message now names what the user typed rather than what it resolved to, which is what
  they can act on. `tests/test_catalog.py` asserts only that the unknown name and the choices
  appear, so this stays true.

- `link` replaces `_ALIASES.get(name, name)` and its `name not in MODULES` check with
  `CATALOG.resolve`. Keep the two refusals distinct: `sushicore` keeps its own message, and the
  message for an unknown module keeps naming the choices and the aliases from `CATALOG`.
- `add` reads `mod = CATALOG[name]` in place of `MODULES[name]`, and the message at
  `services/modules.py:214` reads `CATALOG[name].repo`.

In `services/status_report.py`: replace the `MODULES` import and the `for name in MODULES` at
line 125 with `CATALOG` and `for name in CATALOG`.

In `setup/steps.py`: `owner_order(self._source, MODULES)` becomes
`owner_order(self._source, CATALOG.names())`. Check `owner_order`'s signature first: it takes
something iterable of module names, and a `ModuleCatalog` iterates names, so passing `CATALOG`
directly also works. Pass whichever matches the annotation, and say which in the report.

`BINARY_MODULE` and `SUSHICORE_NAME` stay for now; task 2 removes the first.

- [ ] **Step 5: Rewrite the catalog tests against the interface**

In `sushihub/cli/tests/test_catalog.py`, the assertions move from the dict to `CATALOG`. The six
names, the repo shape, the directory rule and the gitignore lines stay true and stay asserted;
`modules.MODULES` becomes `catalog.CATALOG` and `modules._ALIASES` becomes `CATALOG.aliases()`.
Add two tests the new brick earns:

The second one needs `load_catalog` imported beside `CATALOG`:
`from sushistack.services.catalog import CATALOG, load_catalog`.

```python
def test_the_catalog_resolves_a_name_and_an_alias_to_the_same_module():
    """resolve answers the module name for both spellings and None for neither."""
    assert CATALOG.resolve("sushiruntime") == "sushiruntime"
    assert CATALOG.resolve("sr") == "sushiruntime"
    assert CATALOG.resolve("sushiwater") is None


def test_the_packaged_catalog_is_readable_as_package_data():
    """The catalog loads through importlib.resources, as an installed wheel must."""
    assert load_catalog().names() == CATALOG.names()
```

- [ ] **Step 6: Verify and report**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 336 passed (334 plus the two new tests), with no test changed in meaning.

Run: `python -c "from sushistack.services.catalog import CATALOG; print(CATALOG.names())"`
Expected: the six names in catalog order.

Run: `hub status`
Expected: the same table as before this task, because nothing about behaviour changed.

- [ ] **Step 7: Commit**

```bash
git add sushihub/cli/sushistack/services/catalog.py sushihub/cli/sushistack/catalog.toml sushihub/cli/pyproject.toml sushihub/cli/sushistack/services/modules.py sushihub/cli/sushistack/services/status_report.py sushihub/cli/sushistack/setup/steps.py sushihub/cli/tests/test_catalog.py
git commit -m "refactor(cli): read the module catalog from packaged data"
```

---

### Task 2: The distribution field replaces BINARY_MODULE

**Files:**
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/tests/test_catalog.py`
- Modify: `sushihub/cli/tests/test_add_binary.py`

**Interfaces:**
- Consumes: task 1's `Module.is_binary`.
- Produces: `BINARY_MODULE` no longer exists.

- [ ] **Step 1: Read the entry rather than the name**

In `services/modules.py`:

- Delete `BINARY_MODULE` and the comment block above it, moving what it says into
  `catalog.toml`'s header, which already describes `distribution`.
- At `services/modules.py:392`, `if name == BINARY_MODULE and (binary or not _source_reachable(mod.repo)):`
  becomes `if mod.is_binary and (binary or not _source_reachable(mod.repo)):`.
- At `services/modules.py:400`, the refusal names the binary module from the catalog rather than
  from a constant:

```python
        sold = [n for n in CATALOG if CATALOG[n].is_binary]
        console.error(f"{name}: only {', '.join(sold)} is sold as a binary; every "
                      "other module is open source and is cloned.")
```

  Read the existing sentence before replacing it and keep its second half exactly, so the
  message a user sees changes only where the name comes from.

- [ ] **Step 2: Update the two tests that name the constant**

`tests/test_catalog.py::test_sushiengine_is_the_one_module_sold_as_a_binary` asserts
`modules.BINARY_MODULE == "sushiengine"`. Rewrite it against the field:

```python
def test_sushiengine_is_the_one_module_sold_as_a_binary():
    """Exactly one entry carries distribution = binary, and it is sushiengine."""
    sold = [n for n in CATALOG if CATALOG[n].is_binary]
    assert sold == ["sushiengine"]
```

`tests/test_add_binary.py` imports or references `BINARY_MODULE` in
`test_add_binary_refuses_a_module_that_is_not_sold`. Check with
`grep -n "BINARY_MODULE" sushihub/cli/tests/test_add_binary.py` and update whatever it names.
Do not weaken that test: it is one of the 18 that pin the licensed download path.

- [ ] **Step 3: Verify**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 336 passed.

Run: `grep -rn "BINARY_MODULE" sushihub/cli`
Expected: no hit.

- [ ] **Step 4: Commit**

```bash
git add sushihub/cli/sushistack/services/modules.py sushihub/cli/sushistack/catalog.toml sushihub/cli/tests/test_catalog.py sushihub/cli/tests/test_add_binary.py
git commit -m "refactor(cli): decide source or binary from the catalog entry"
```

---

### Task 3: sushidsp and sushitrack leave the stack

**Files:**
- Modify: `sushihub/cli/sushistack/catalog.toml`
- Modify: `sushihub/cli/tests/test_catalog.py`
- Modify: `sushihub/cli/tests/test_link.py`
- Modify: `docs/architecture/WORKSPACE.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: task 2's catalog.
- Produces: a four-module stack. `hub add sushidsp` reports an unknown module.

- [ ] **Step 1: Delete the two tables**

Remove the `[sushidsp]` and `[sushitrack]` tables from `catalog.toml`. Nothing else changes:
every reader already asks the catalog.

- [ ] **Step 2: Follow the change through the tests**

In `tests/test_catalog.py`:
- `test_the_catalog_holds_the_six_modules_of_today` becomes
  `test_the_catalog_holds_the_four_stack_modules`, asserting
  `["sushiruntime", "sushiengine", "sushiai", "sushiblas"]`. Rewrite its docstring: the sentence
  about wave 2 dropping two modules has come true and should now say what the list is.
- Add the test that states the removal rather than leaving it as an absence:

```python
def test_sushidsp_and_sushitrack_are_not_stack_modules():
    """The two products that share no dependency with the stack are not in the catalog."""
    assert CATALOG.resolve("sushidsp") is None
    assert CATALOG.resolve("sushitrack") is None
    assert CATALOG.resolve("sd") is None
    assert CATALOG.resolve("st") is None
```

In `tests/test_link.py`, `test_link_refuses_a_name_outside_the_catalog` asserts the full
sentence, including all six names and all six aliases. Update both lists to the four that remain.

- [ ] **Step 3: Say what happens to an existing link**

This is the part a user feels. `sushihub/cli/modules.local.toml` on a developer's machine may
link `sushidsp` or `sushitrack`; the maintainer's does today. After this task those entries are
inert: `hub status` stops listing them, `hub update` stops pulling them, and nothing reports
that they were dropped.

Dependency aggregation is not affected, and this was verified rather than assumed:
`setup/dependency_source.py:156` walks the workspace directories and `:164` walks
`registered_modules()`, neither of which consults the catalog. A linked `sushidsp` that carried
a `cli/sushistack.deps.toml` would still contribute it. Neither of the two carries one.

Add to `docs/getting_started/INSTALL.md`, under the existing upgrade section:

```markdown
### sushidsp and sushitrack left the stack on 2026-09-22

They share no dependency with `sushiruntime`, `sushiblas`, `sushiai` and `sushiengine`, and are
their own products with their own CLIs, `sd` and `st`. `hub` no longer knows them: `hub add
sushidsp` reports an unknown module, and a `sushidsp` line left in
`sushihub/cli/modules.local.toml` is ignored rather than honoured. Delete the line by hand; the
checkout itself is untouched and `sd` keeps working.
```

- [ ] **Step 4: Update the manual**

- `docs/architecture/WORKSPACE.md` draws the workspace tree with `sushidsp/` in it. Remove that
  line and check whether the prose around it still counts modules correctly.
- `README.md` names what the workspace holds; check it and correct any count.

Run `grep -rn "sushidsp\|sushitrack" README.md docs/ --include=*.md | grep -v docs/agent` and
resolve every hit that presents them as stack modules. Hits that name them as separate products
are correct and stay.

- [ ] **Step 5: Verify**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 337 passed (336 plus the new removal test).

Run: `hub add sushidsp --dry-run`
Expected: the unknown-module message, naming the four remaining modules and their four aliases.

Run: `hub status`
Expected: four module rows plus the `sushicore` row. The linked `sushidsp` and `sushitrack` no
longer appear, which is the change, not a fault.

- [ ] **Step 6: Commit**

```bash
git add sushihub/cli/sushistack/catalog.toml sushihub/cli/tests/test_catalog.py sushihub/cli/tests/test_link.py docs/architecture/WORKSPACE.md docs/getting_started/INSTALL.md README.md
git commit -m "feat(cli)!: take sushidsp and sushitrack out of the stack"
```

---

### Task 4: The sushicore refusal tells the truth

`link` refuses `sushicore` with "sushicore ships inside this repository and cannot be linked.
Edit it in place, at `sushicore/`." Wave 1 made both sentences false: it ships from PyPI and
there is no `sushicore/` to edit. `tests/test_link.py` pins the sentence, so the test is what
makes this visible.

**Files:**
- Modify: `sushihub/cli/sushistack/services/modules.py`
- Modify: `sushihub/cli/tests/test_link.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no interface change; one message changes.

- [ ] **Step 1: Correct the message**

At `services/modules.py:447`:

```python
        console.error(f"{SUSHICORE_NAME} is not a stack module: it is a package every "
                      "Sushi CLI installs from PyPI. To work on it, install your "
                      "checkout over the release with `pip install -e <path>`.")
```

- [ ] **Step 2: Follow it in the test**

`tests/test_link.py::test_link_refuses_sushicore` asserts the old sentence. Replace the expected
text with the new one, keeping the assertion that nothing is written to the registry.

- [ ] **Step 3: Verify**

Run: `python -m pytest sushihub/cli/tests -q`
Expected: 337 passed.

Run: `hub link sushicore .`
Expected: the new message, exit code 1, and `sushihub/cli/modules.local.toml` unchanged.

- [ ] **Step 4: Close the wave**

`docs/design/REMAINING_WORK.md`: the decoupling table's wave 2 row gains `Landed 2026-09-22.`
`docs/design/WORKSPACE_DECOUPLING.md`: the wave 2 row's acceptance column records the same.

Add to `docs/reference/CHANGELOG.md`:

```
- 2026-09-22 — Read the module catalog from packaged data instead of a dict in code (`sushihub/cli/sushistack/services/catalog.py`, `sushihub/cli/sushistack/catalog.toml`).
- 2026-09-22 — Took sushidsp and sushitrack out of the stack catalog (`sushihub/cli/sushistack/catalog.toml`).
```

- [ ] **Step 5: Commit**

```bash
git add sushihub/cli/sushistack/services/modules.py sushihub/cli/tests/test_link.py docs/design/REMAINING_WORK.md docs/design/WORKSPACE_DECOUPLING.md docs/reference/CHANGELOG.md
git commit -m "fix(cli): say where sushicore actually lives when a link is refused"
```

---

## Order

```
Task 1  ->  Task 2  ->  Task 3  ->  Task 4
```

Strictly serial: all four edit `services/modules.py` and `tests/test_catalog.py`, so no two can
run at once. Each ends green, so the chain can stop after any of them.
