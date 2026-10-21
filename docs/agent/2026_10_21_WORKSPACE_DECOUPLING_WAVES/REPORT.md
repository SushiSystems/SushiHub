# Workspace decoupling: the waves that landed

**Status:** Shipped — 2026-10-21

The landing records of waves 0 to 7 of the workspace decoupling and the measurements behind its
decisions. The design document [Decoupling the hub from the SushiStack
checkout](../../design/WORKSPACE_DECOUPLING.md) took them out when it took the design format.

## Waves

Waves 0 to 6 landed on 2026-09-22, and wave 7 all but its `st setup` task. Each plan is under
`docs/archive/agent/plans/`.

| Wave | Landed | Met when |
| --- | --- | --- |
| 0 | 2026-09-22 | 37 tests across five modules, the suite at 334 |
| 1 | 2026-09-22 | `sushicore==0.1.0` on PyPI, installed from the index by `hub` and by all six consumer repositories |
| 2 | 2026-09-22 | `hub add all` names four modules, `hub add sushidsp` reports an unknown module, and the suite is at 337 |
| 3 | 2026-09-22 | `hub init` then `hub install --dry-run` ran to completion in an empty directory with no `sushihub/` anywhere, and this workspace upgraded in place, keeping all five `[modules]` entries and eleven probed tool paths |
| 4 | 2026-09-22 | `sushihub` 0.1.0 on PyPI; `install.ps1` ran end to end in a directory that was no checkout, installing from the index and provisioning; a venv install from the index ran `hub init` and `hub install --dry-run` with no `sushihub/` anywhere |
| 5 | 2026-09-22 | `hub gui build` exited 0 and `hub gui test` passed 37 of 37, including the case that reads the re-recorded payload |
| 6 | 2026-09-22 | A `sushidsp` checkout carrying a manifest, with no catalog entry, was listed by `hub status` with its real branch |
| 7 | 2026-09-22, except `st setup` | `hub status` lists `sushidsp` and `hub doctor` attributes `sdl2` to it, with zero mentions of `sushidsp` in `catalog.toml` |

Plans: `2026-09-22-wave-3-workspace-directory.md`, `2026-09-22-wave-4-hub-on-pypi.md`,
`2026-09-22-wave-5-the-application-sees-today.md`, `2026-09-22-wave-6-a-module-describes-itself.md`,
`2026-09-22-wave-7-sd-and-st-stand-on-their-own.md`, and `2026-09-22-rename-to-sushihub.md` for
the rename.

Wave 3 chose one `workspace.toml` rather than the three files the design named. Wave 5 left the
application unchanged: it already read every field the payload carries and names neither removed
row.

## Breaking changes that shipped

- Wave 2 took `sushidsp` and `sushitrack` out of `hub add`, `hub link` and `hub install-cli`.
- Wave 3 moved the workspace's data into `.sushistack/workspace.toml`.
- The tool's own name changed: the import package became `sushihub` and the CLI, the application
  and the contract moved to the repository root. `hub` went to 0.2.0: below 1.0 a breaking change
  is a minor bump, and 1.0.0 would declare the interface settled, which it is not.

## Measurements

- 2026-09-21: `cli/tests` held 24 files and 297 passing tests, and `.github/workflows/ci.yml:43`
  ran them. The source-or-binary decision was the best covered part of the code, with 18 tests in
  `tests/test_add_binary.py`, covering the clone, the out-of-reach fallback, the forced binary,
  the missing licence, the hash mismatch and the update path.
- Five seams the design rewrites carried no test: `config_dir`, `MODULES`, `_GITIGNORE_LINES`,
  `sushicore_dir` and `_install_module_cli`. `hub init` and `hub link` were exercised only
  incidentally through `tests/test_json_streams.py`. Wave 0 covered those five and nothing else.
- 2026-09-22: no file in `sushidsp` or `sushitrack` mentions SYCL.
- 2026-09-21: `pypi.org/simple/` answered 404 for `sushicore`, `sushihub`, `sushistack`,
  `sushiruntime`, `sushiengine`, `sushiai`, `sushiblas`, `sushidsp` and `sushitrack`, so all nine
  were free. They are unreserved until the first upload, so wave 1 uploaded a placeholder
  `sushicore` before anything else in that wave.
- The desktop application is about 3 MB (`sushihub_gui.exe` 2.4 MB plus `glfw3.dll` 484 KB), not
  the 262 MB build tree beside it.

## Dated decisions

- 2026-09-22, the owner: `sushidsp`'s real-time path stays on the CPU, because the circuit solve
  is sample-serial and a nonlinearity inside a feedback loop would not survive floating point
  that differs between machines.
- 2026-09-22, the owner: the module CLIs are not published; the desktop application ships as its
  own `sushihub-gui` distribution.
- 2026-10-04: `hub` became optional for building a module; the toolchain selection rule and the
  base fragment moved to sushicore, and a bare `hub install` installs one SYCL toolchain where it
  installed three.
- 2026-10-21, the owner: `sushitrack` is in the catalog again, with `st` as its alias.
