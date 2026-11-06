# Test review: report

**Status:** Open — every test has a verdict; the plan's jobs are next

Every test in the repository has a verdict from `skills/testing/REVIEWING.md` of SushiSkills, reviewed
on 2026-11-05 as part of J15 (`docs/agent/2026_11_03_INDUSTRIAL_TESTING/` in SushiSkills). The review read
the code and ran nothing. Each record names the files it read.

## What the review found

146 of 400 tests are kept. Most of the rest replace the repository's own functions rather than reach
them through a port:

- Tests replace `session.client`, `git_ops.run`, `links.registered`, `modules.deps_dir`,
  `module_fragments.present_modules`, `pipx.installed`, `pins.workspace_root` and
  `releases.host_platform`, or read underscore names. There is no in-memory port for git, the session
  client, pipx or the release host.
- Recorder spies on `modules.console`. The console is not a declared port; the plan gives it an
  in-memory console adapter and moves the recorders onto it.
- Loops and comprehensions in test bodies, which become rows.
- No gui suite carries a size prefix, so all 37 gui tests fail the size rule.
- `test_selection`'s `build_pipeline` reaches `workspace_root()`.

## Decisions

The owner delegated these decisions on 2026-11-05. Each ruling below is final for the plan; its reason follows it.

1. Ports for git, the session client, pipx, the release host and the console, each with an in-memory adapter: yes. Every seam is added as a parameter or overload whose default keeps today's behaviour, so existing callers compile unchanged and the change is a minor version. A value passed in is preferred to a reset of process-wide state.
2. The two deletes in `test_migrate_command.py` stand. Chunk 002 read the sibling that covers them.
3. T1, ruled by the lead on 2026-11-07: the five ports are Protocols in `cli/sushihub/services/ports.py`, carried as one `Ports` value that each command takes as a `ports` keyword, `Ports.machine()` when left out. One value rather than five parameters, because every command that reaches one port reaches the console too and the list would grow with each port. The in-memory console is sushicore's `RecordingConsole`, so the floor of `sushicore` rises to 0.10.12, the first release that ships it. The machine adapters call the module functions by name at call time, so the tests M1 has not rewritten yet keep passing.
4. T2 and M2 change gui C++ tests, which only a build proves. The 2026-11-07 lead may not build, so both wait. The size checker reads only C++ files named `test_*`, so it reads no gui suite today; KI-21 records it.

## Dispatches

dispatch: J15 review, 2 chunks — haiku high, 1 round each, passed, rung 1

## Totals

| Tests | Keep | Rewrite | Resize | Split | Merge | Delete | Characterize | Add |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 400 | 146 | 132 | 48 | 33 | 32 | 9 | 0 | 11 |

Kept as they stand: 146 of 400 (36%).

## Verdicts by question

| Verdict | Question | What it means | Tests |
| --- | --- | --- | --- |
| rewrite | 1 | a forbidden kind | 114 |
| resize | 8 | wrong size | 48 |
| split | 3 | no single promise | 33 |
| merge | 4 | a duplicate | 32 |
| delete | 1 | a forbidden kind | 8 |
| rewrite | 6 | oracle is the code | 7 |
| rewrite | 7 | a long-test sign | 6 |
| rewrite | 2 | cannot fail | 4 |

## Modules

| Module | Files | Tests | Keep | Rewrite | Resize | Split | Merge | Delete | Characterize |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cli` | 34 | 363 | 146 | 125 | 33 | 21 | 31 | 7 | 0 |
| `gui` | 5 | 37 | 0 | 7 | 15 | 12 | 1 | 2 | 0 |

## Records

One line per test: `file::test | verdict | question | reason | files read`.

### `cli/tests/test_add_binary.py`

```
test_add_clones_sushiengine_when_its_repository_answers | rewrite | 1 | modules.add: a module whose repository answers is cloned; replaces git_ops.run and git_ops.source_reachable, the adapter has no port | cli/tests/test_add_binary.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_installs_the_binary_when_the_repository_is_out_of_reach | rewrite | 1 | modules.add: sushiengine from its release when out of reach; replaces source_reachable, pipx.installed, modules._install_module_cli, links.registered, workspace_root; four facts in one test | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/tests/test_releases.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_binary_installs_it_even_when_the_source_is_in_reach | rewrite | 1 | modules.add: binary=True installs the release when the source is reachable; replaces source_reachable and the workspace fixture | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/tests/test_releases.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_names_both_ways_in_when_neither_is_open | rewrite | 1 | modules.add: names both ways in when neither source nor login is open; replaces source_reachable and session.client | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_binary_without_a_session_asks_for_the_login_alone | rewrite | 1 | modules.add: binary without a session asks for the login alone; replaces session.client and the workspace fixture | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/modules.py
test_add_binary_refuses_a_module_that_is_not_sold | rewrite | 1 | modules.add: binary refuses a module the catalog does not sell; the workspace fixture replaces workspace_root, links.registered, git_ops.run, source_reachable, pipx.installed | cli/tests/test_add_binary.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_reports_a_licence_the_account_does_not_hold | rewrite | 1 | modules.add: a licence the account does not hold refuses the install; replaces source_reachable and session.client | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_refuses_a_download_whose_hash_does_not_match | rewrite | 1 | modules.add: a sha256 mismatch refuses the install; replaces source_reachable and the workspace fixture; the verify-level promise is in test_releases.py but not at add level | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/tests/test_releases.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_dry_run_says_it_would_install_the_release | rewrite | 1 | modules.add: a dry-run binary install says it would install and writes nothing; replaces source_reachable, session.client and the workspace fixture | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_leaves_an_installed_binary_alone | delete | 1 | same promise as cli/tests/test_add_provisions.py::test_add_leaves_a_binary_module_alone, which is kept and rewritten; this copy replaces workspace_root, links.registered, git_ops.run and _install_module_cli | cli/tests/test_add_binary.py;cli/tests/test_add_provisions.py;cli/sushihub/services/modules.py
test_update_says_a_binary_install_is_already_the_latest | rewrite | 1 | modules.update: a binary at the latest release says so; replaces binary.releases.host_platform, session.client and the workspace fixture | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/tests/test_releases.py;cli/sushihub/services/modules.py
test_update_downloads_a_newer_release_and_writes_the_licence_again | rewrite | 1 | modules.update: a newer release is downloaded and the licence written again; replaces binary.releases.host_platform, session.client and the workspace fixture | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/tests/test_releases.py;cli/sushihub/services/modules.py
test_update_asks_for_a_login_before_refreshing_a_binary_install | rewrite | 1 | modules.update: asks for a login before refreshing a binary; replaces session.client and the workspace fixture | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/modules.py
test_write_licence_returns_the_expiry_and_writes_the_bare_token | rewrite | 1 | licence_file.write_licence: returns the expiry and writes the bare token; sign_in replaces session.client although the client is passed in directly, so the replacement is unused | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/licence_file.py
test_read_licence_expiry_reads_the_exp_claim | resize | 8 | licence_file.read_licence_expiry: the exp claim becomes an ISO time; decision on values reached only through a file, so the seam is a parse of the token text, then small | cli/tests/test_add_binary.py;cli/sushihub/services/licence_file.py
test_read_licence_expiry_is_none_without_a_file | keep | 9 | licence_file.read_licence_expiry: absent file gives None; the filesystem answer is the boundary, so medium is the right size | cli/tests/test_add_binary.py;cli/sushihub/services/licence_file.py
test_read_licence_expiry_is_none_when_the_token_is_not_a_jwt | resize | 8 | licence_file.read_licence_expiry: a token that is not a JWT gives None; decision on values, seam needed | cli/tests/test_add_binary.py;cli/sushihub/services/licence_file.py
test_read_licence_expiry_is_none_when_the_payload_names_no_expiry | resize | 8 | licence_file.read_licence_expiry: a payload with no exp gives None; decision on values, seam needed | cli/tests/test_add_binary.py;cli/sushihub/services/licence_file.py
test_a_binary_install_reports_a_credential_store_it_cannot_read[act] | rewrite | 1 | binary.add and binary.update: report an unreadable credential store once and return False; replaces session.client with a stub client; parametrised over two acts | cli/tests/test_add_binary.py;cli/tests/test_identity.py;cli/sushihub/services/binary.py
```

### `cli/tests/test_add_provisions.py`

```
test_add_provisions_once_after_a_new_clone | rewrite | 1 | modules.add: provisioning runs once after a new clone; replaces workspace_root, links.registered, git_ops.run and _install_module_cli | cli/tests/test_add_provisions.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_skips_provision_when_nothing_new | rewrite | 1 | modules.add: provisioning is skipped when nothing new was cloned; replaces workspace_root, links.registered and _install_module_cli | cli/tests/test_add_provisions.py;cli/sushihub/services/modules.py
test_add_honours_skip_install | rewrite | 1 | modules.add: skip_install skips provisioning; replaces workspace_root, links.registered, git_ops.run and _install_module_cli | cli/tests/test_add_provisions.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
test_add_leaves_a_binary_module_alone | rewrite | 1 | modules.add: a binary module is left alone with no clone and no provision; survivor of the duplicate in test_add_binary.py; replaces workspace_root, links.registered, git_ops.run and _install_module_cli | cli/tests/test_add_provisions.py;cli/sushihub/services/modules.py;cli/sushihub/services/git_ops.py
```

### `cli/tests/test_catalog.py`

```
test_the_catalog_holds_the_eight_stack_modules | rewrite | 6 | catalog: the stack modules in fixed order; the expected list is the catalog.toml data copied into the test, not an independently derived oracle | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_every_entry_names_its_repository_and_directory | rewrite | 7 | catalog: each entry carries its repository URL and directory; a loop over CATALOG in the body; rows instead | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_sushiengine_is_the_one_module_sold_as_a_binary | rewrite | 7 | catalog: exactly one binary module; a comprehension loop in the body | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_sushicore_is_not_a_catalog_member | rewrite | 6 | catalog: sushicore is not a member; the oracle is modules.SUSHICORE_NAME, a constant of the code under test; the literal name is the oracle | cli/tests/test_catalog.py;cli/sushihub/services/modules.py;cli/sushihub/services/catalog.py
test_every_module_has_a_two_letter_alias | rewrite | 2 | catalog: every alias maps to its module; the name promises two-letter aliases but no length is asserted, so a three-letter alias passes | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_an_empty_list_means_every_module | rewrite | 1 | modules._resolve_names: an empty list or all expands to the catalog; reaches the private _resolve_names; drive through the public add or update | cli/tests/test_catalog.py;cli/sushihub/services/modules.py
test_aliases_expand_to_module_names | rewrite | 1 | modules._resolve_names: aliases expand in the order given; reaches the private _resolve_names | cli/tests/test_catalog.py;cli/sushihub/services/modules.py
test_a_name_outside_the_catalog_is_refused | rewrite | 1 | modules._resolve_names: an unknown name returns None and names the choices; reaches the private _resolve_names; the message is already tested through link in test_link.py | cli/tests/test_catalog.py;cli/tests/test_link.py;cli/sushihub/services/modules.py
test_the_gitignore_lines_cover_every_module_and_the_workspace_directory | rewrite | 1 | modules: init's gitignore lines cover every module and the workspace directory; reaches the private _GITIGNORE_LINES; assert the file init writes instead | cli/tests/test_catalog.py;cli/tests/test_init.py;cli/sushihub/services/modules.py
test_the_gitignore_lines_name_no_file_a_new_workspace_never_writes | rewrite | 1 | modules: no line for files a new workspace never writes; reaches the private _GITIGNORE_LINES and pins a dated history rather than a promise | cli/tests/test_catalog.py;cli/sushihub/services/modules.py
test_sushidsp_is_a_stack_module_reached_by_name_and_alias | merge | 4 | catalog: resolves a name and an alias to the same module; merge with test_sushitrack_is_a_stack_module_reached_by_name_and_alias and test_the_catalog_resolves_a_name_and_an_alias_to_the_same_module | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_sushitrack_is_a_stack_module_reached_by_name_and_alias | merge | 4 | catalog: resolves a name and an alias to the same module; merge with test_sushidsp_is_a_stack_module_reached_by_name_and_alias and test_the_catalog_resolves_a_name_and_an_alias_to_the_same_module | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_the_catalog_resolves_a_name_and_an_alias_to_the_same_module | merge | 4 | catalog: resolves a name and an alias to the same module, and None for an unknown name; merge with test_sushidsp_is_a_stack_module_reached_by_name_and_alias and test_sushitrack_is_a_stack_module_reached_by_name_and_alias | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
test_the_packaged_catalog_is_readable_as_package_data | rewrite | 1 | catalog: the packaged catalog loads through importlib.resources; a small test reaches a file, which small forbids; move it to medium or inject the text | cli/tests/test_catalog.py;cli/sushihub/services/catalog.py
```

### `cli/tests/test_cli_install.py`

```
test_a_module_without_a_cli_package_is_skipped | rewrite | 1 | modules._install_module_cli: a module without cli/pyproject.toml is skipped; reaches the private name; replaces pipx.command with a failing lambda | cli/tests/test_cli_install.py;cli/sushihub/services/modules.py;cli/sushihub/services/pipx.py
test_a_missing_pipx_is_a_warning | rewrite | 1 | modules._install_module_cli: a missing pipx is a warning naming the later command; reaches the private name; replaces pipx.command | cli/tests/test_cli_install.py;cli/sushihub/services/modules.py;cli/sushihub/services/pipx.py
test_the_happy_path_installs_the_module_cli_editable | rewrite | 1 | modules._install_module_cli: installs editable with pipx; reaches the private name; replaces the pipx subprocess seam from a modules-level test | cli/tests/test_cli_install.py;cli/sushihub/services/modules.py;cli/sushihub/services/pipx.py
test_a_failed_pipx_install_is_reported | rewrite | 1 | modules._install_module_cli: a failed pipx install is reported; reaches the private name; replaces pipx.command and the subprocess seam | cli/tests/test_cli_install.py;cli/sushihub/services/modules.py;cli/sushihub/services/pipx.py
test_both_paths_install_a_module_cli_the_same_way | rewrite | 1 | modules._install_module_cli and pipx.install: the two paths leave the same install; reaches the private name; compares two calls that may be one path | cli/tests/test_cli_install.py;cli/sushihub/services/modules.py;cli/sushihub/services/pipx.py
```

### `cli/tests/test_core_pin.py`

```
test_rewrite_sets_the_exact_form_whatever_the_operator_was | rewrite | 7 | core_pin.rewrite_requirement: any operator becomes ==version; a loop over operators in the body; rows instead | cli/tests/test_core_pin.py;cli/sushihub/services/core_pin.py
test_rewrite_refuses_a_file_without_the_requirement | resize | 8 | core_pin.rewrite_requirement: a file with no requirement raises ValueError; pure text function in a medium file, small sees it | cli/tests/test_core_pin.py;cli/sushihub/services/core_pin.py
test_pin_rewrites_every_module_and_the_hub_itself | rewrite | 1 | core_pin.move_core_pin: every module and the hub move, CRLF survives; the fixture replaces module_fragments.present_modules, core_pin.present_modules and core_pin.workspace_root | cli/tests/test_core_pin.py;cli/sushihub/services/core_pin.py;cli/sushihub/services/module_fragments.py;cli/sushihub/services/pins.py
test_a_dry_run_writes_nothing | rewrite | 1 | core_pin.move_core_pin: a dry run writes nothing; the fixture replaces present_modules | cli/tests/test_core_pin.py;cli/sushihub/services/core_pin.py;cli/sushihub/services/module_fragments.py
test_a_project_already_on_the_version_is_not_reported | rewrite | 1 | core_pin.move_core_pin: a second run changes nothing; the fixture replaces present_modules | cli/tests/test_core_pin.py;cli/sushihub/services/core_pin.py;cli/sushihub/services/module_fragments.py
test_a_version_that_is_not_a_release_number_is_refused[version] | rewrite | 1 | core_pin.pin: a non-release version is refused; the workspace fixture replaces repository functions this test never calls; the check is pure | cli/tests/test_core_pin.py;cli/sushihub/services/core_pin.py;cli/sushihub/services/pins.py
```

### `cli/tests/test_dependency_fragment.py`

```
test_every_dependency_carries_the_module_that_declared_it | rewrite | 1 | dependency_source: the owner comes from the module name; reaches the private _parse_manifest | cli/tests/test_dependency_fragment.py
test_the_module_table_still_yields_depends_on | rewrite | 1 | dependency_source: depends_on is read from the module table; reaches the private _parse_manifest | cli/tests/test_dependency_fragment.py
test_a_shape_the_reader_refuses_still_stops_hub | rewrite | 1 | dependency_source: an unreadable shape raises ValueError naming the file; reaches the private _parse_manifest | cli/tests/test_dependency_fragment.py
test_a_dependency_that_names_no_owner_belongs_to_the_shared_set | rewrite | 1 | dependency_source: no owner means the shared set; reaches the private _parse_manifest | cli/tests/test_dependency_fragment.py
test_the_fragments_this_package_ships_all_read | rewrite | 1 | dependency_source: every packaged fragment parses; reaches the private _parse_manifest and loops over fragments in the body | cli/tests/test_dependency_fragment.py
```

### `cli/tests/test_describe.py`

```
test_catalogue_validates_against_its_schema | delete | 1 | describe.catalogue against its schema; a small test reads contract/describe.schema.json through a helper, which small forbids; the same promise is in cli/tests/test_json_streams.py::test_describe_prints_a_valid_catalogue | cli/tests/test_describe.py;cli/tests/test_json_streams.py;cli/sushihub/describe.py
test_every_registered_command_appears_once_sorted | rewrite | 2 | describe.catalogue: each command once, sorted; the body never checks uniqueness, so a duplicated name passes | cli/tests/test_describe.py;cli/sushihub/describe.py
test_add_is_described_with_its_argument_and_flags | split | 3 | describe.catalogue: the add command describes its argument and its flags, and its help has no markup; three promises joined by and | cli/tests/test_describe.py;cli/sushihub/describe.py
test_a_nested_group_is_listed_by_its_children | merge | 4 | describe.catalogue: a group is listed by its children, not by its own name; merge with cli/tests/test_docs_command.py::test_the_catalogue_lists_docs_bundle_and_not_the_bare_group | cli/tests/test_describe.py;cli/tests/test_docs_command.py;cli/sushihub/describe.py
test_gui_build_is_described_with_its_type_choice_and_its_defines | split | 3 | describe.catalogue: the choice, the boolean and the multiple define flag are three promises joined by and | cli/tests/test_describe.py;cli/sushihub/describe.py
test_the_catalogue_is_the_shared_one_with_hubs_distribution_and_presences | rewrite | 6 | describe.catalogue: hub's catalogue equals sushicore's called with hub's arguments; the oracle is the code under test called again | cli/tests/test_describe.py;cli/sushihub/describe.py
test_a_hidden_command_is_left_out_of_the_catalogue | keep | 9 | describe.catalogue: a hidden command is omitted; a local Typer app, in process, no boundary | cli/tests/test_describe.py;cli/sushihub/describe.py
test_describe_prints_the_catalogue_as_one_compact_utf8_line | rewrite | 6 | describe.catalogue output: compact UTF-8 JSON and one newline; the expected bytes are the code's own catalogue re-serialised | cli/tests/test_describe.py;cli/sushihub/describe.py
test_describe_lists_every_visible_command_and_no_hidden_one | rewrite | 1 | describe.catalogue: the visible commands; the set of 23 names is pasted from current output, a golden nobody derived; derive it from the Typer app | cli/tests/test_describe.py;cli/sushihub/describe.py
test_no_command_help_repeats_a_stale_count_or_the_old_sushicore_delivery | keep | 9 | help text of four commands carries none of four stale claims; each check fails when its claim returns | cli/tests/test_describe.py
```

### `cli/tests/test_docs_command.py`

```
test_bundle_without_a_release_exits_two_and_names_the_option | keep | 9 | docs bundle without --release exits 2 and names the option; command body not read, so the size is kept unverified | cli/tests/test_docs_command.py
test_bare_docs_prints_the_group_help_and_exits_two | keep | 9 | docs group with no subcommand exits 2 and lists bundle; command body not read, so the size is kept unverified | cli/tests/test_docs_command.py
test_the_catalogue_lists_docs_bundle_and_not_the_bare_group | merge | 4 | describe.catalogue: a group is listed by its children; merge with cli/tests/test_describe.py::test_a_nested_group_is_listed_by_its_children | cli/tests/test_docs_command.py;cli/tests/test_describe.py;cli/sushihub/describe.py
test_checkout_root_is_the_nearest_ancestor_that_holds_a_publish_list | keep | 9 | cli.checkout_root: walks up to the nearest publish list; the walk is a file-system answer, so medium is the boundary | cli/tests/test_docs_command.py
test_checkout_root_outside_a_checkout_raises_the_hub_error | keep | 9 | cli.checkout_root: raises HubError outside a checkout; file-system answer, medium | cli/tests/test_docs_command.py
test_bundle_outside_a_checkout_gives_one_line_and_exit_one | keep | 9 | docs bundle outside a checkout: one error line and exit 1 as a single outcome, no traceback | cli/tests/test_docs_command.py
test_bundle_outside_a_checkout_under_json_ends_in_one_failed_result | rewrite | 6 | docs bundle outside a checkout under --json: one error event and one failed result; the expected message is cli.K_NO_CHECKOUT, a constant of the code under test | cli/tests/test_docs_command.py
test_bundle_writes_the_archive_of_the_checkout_it_runs_in | keep | 9 | docs bundle: writes the archive and its sha256 in the checkout it runs in; files on disk, medium | cli/tests/test_docs_command.py
test_bundle_under_json_streams_valid_events_and_ends_in_one_result | split | 3 | docs bundle under --json: every event validates, and the stream ends in one result; two promises that can break apart | cli/tests/test_docs_command.py
```

### `cli/tests/test_doctor_table.py`

```
test_summarize_counts_each_status_under_its_own_text | keep | 9 | DetectStep.summarize_inventory: counts each status under its own text | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_summarize_leaves_out_a_status_no_row_carries | keep | 9 | DetectStep.summarize_inventory: a status no row carries is left out | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_summarize_counts_an_unforeseen_status_under_its_own_text | keep | 9 | DetectStep.summarize_inventory: an unforeseen status keeps its own text | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_summarize_returns_the_missing_rows_in_table_order | keep | 9 | DetectStep.summarize_inventory: missing rows come back in table order | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_prints_groups_then_summary_then_attention_list | split | 3 | doctor output: groups, summary and attention list in that order, and no cuda row in the attention list; three promises joined by then | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_prints_no_attention_list_when_nothing_is_missing | keep | 9 | doctor output: no attention list when nothing is missing | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_keeps_brackets_in_a_missing_detail_on_a_terminal | keep | 9 | doctor output: brackets in a missing detail survive on a terminal | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_json_table_event_is_the_ungrouped_one | rewrite | 6 | doctor JSON: the table event carries no group_by; the test emits its own table and compares it with the run's table, so part of the oracle is the code under test | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_json_carries_summary_and_attention_as_line_events | split | 3 | doctor JSON: the summary and the attention list arrive as line events; two promises that can break apart | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_json_message_holds_a_bracketed_detail_unescaped | keep | 9 | doctor JSON: a bracketed detail is not escaped in the message | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
test_doctor_reports_success_whatever_is_missing[machine] | keep | 9 | doctor: returns OK whatever is missing, on terminal and JSON | cli/tests/test_doctor_table.py;cli/sushihub/setup/steps.py
```

### `cli/tests/test_entry_point.py`

```
test_a_malformed_theme_config_gives_one_line_and_exit_one | keep | 9 | entry point: a malformed theme file gives one error line and exit 1, a single outcome | cli/tests/test_entry_point.py
test_a_malformed_workspace_file_gives_one_line_and_exit_one | rewrite | 2 | entry point: a malformed workspace file gives one line; the body never counts lines, so a multi-line message passes | cli/tests/test_entry_point.py
test_a_malformed_theme_config_under_json_still_ends_in_one_result | keep | 9 | entry point: under --json a malformed theme file still ends in one failed result | cli/tests/test_entry_point.py
test_a_command_outside_a_workspace_gives_one_line_and_exit_one | keep | 9 | entry point: a command outside a workspace gives one error line and exit 1 | cli/tests/test_entry_point.py
test_a_command_outside_a_workspace_under_json_ends_in_one_failed_result | keep | 9 | entry point: under --json a command outside a workspace ends in one failed result | cli/tests/test_entry_point.py
test_gui_without_its_sources_under_json_ends_in_one_failed_result | keep | 9 | entry point: gui clean without sources under --json ends in one failed result | cli/tests/test_entry_point.py
test_a_successful_command_exits_zero | keep | 9 | entry point: a successful command exits 0 | cli/tests/test_entry_point.py
test_an_account_command_without_a_keyring_gives_one_line_and_exit_one[command] | rewrite | 1 | entry point: a missing keyring gives one error line and exit 1 for each account command; replaces session.client and the keyring module functions | cli/tests/test_entry_point.py;cli/tests/test_identity.py;cli/sushihub/services/session.py
test_version_prints_the_distribution_and_exits_zero | keep | 9 | entry point: --version prints the distribution and exits 0 | cli/tests/test_entry_point.py
test_version_is_listed_on_the_help_screen | keep | 9 | entry point: --version is listed on the root help | cli/tests/test_entry_point.py
test_the_module_entry_runs_main | rewrite | 5 | entry point: python -m sushihub runs main; the test checks an attribute identity, so a wrapper with the same behaviour fails it | cli/tests/test_entry_point.py
```

### `cli/tests/test_fetched_sources.py`

```
test_the_newest_copy_is_chosen_by_release_order | keep | 9 | fetched_sources.newest_copy: the copy with the highest release wins; medium for the git copies on disk | cli/tests/test_fetched_sources.py
test_a_copy_no_module_pins_is_unused | rewrite | 1 | fetched_sources.unused_copies: a copy no module pins is unused; the workspace fixture replaces module_fragments.present_modules | cli/tests/test_fetched_sources.py;cli/sushihub/services/module_fragments.py
test_clean_removes_only_the_unused_copy | rewrite | 1 | fetched_sources.clean: removes only the unused copy; the workspace fixture replaces module_fragments.present_modules | cli/tests/test_fetched_sources.py;cli/sushihub/services/module_fragments.py
test_a_dry_run_clean_removes_nothing | rewrite | 1 | fetched_sources.clean: a dry run removes nothing; the workspace fixture replaces module_fragments.present_modules | cli/tests/test_fetched_sources.py;cli/sushihub/services/module_fragments.py
test_a_module_is_cloned_from_the_copy_with_the_repository_as_its_remote | keep | 9 | fetched_sources.clone_from_copy: the clone's origin is the repository, not the copy; real git on disk | cli/tests/test_fetched_sources.py
```

### `cli/tests/test_git_state.py`

```
test_reads_nothing_from_a_directory_that_is_not_a_checkout | keep | 9 | git_state.read_git_state: nothing from a non-checkout; real git on disk | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_reads_nothing_from_a_subdirectory_of_someone_elses_checkout | keep | 9 | git_state.read_git_state: nothing from a subdirectory of another checkout | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_reports_no_upstream_as_null_counts | split | 3 | git_state.read_git_state: the branch name and the null ahead and behind counts are two promises | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_counts_local_commits_as_ahead | keep | 9 | git_state.read_git_state: local commits count as ahead | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_counts_behind_only_after_a_fetch | keep | 9 | git_state.read_git_state: behind counts only after a fetch | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_reports_a_detached_head_as_no_branch | keep | 9 | git_state.read_git_state: a detached head reports no branch | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_reports_no_last_fetch_for_a_checkout_never_fetched | keep | 9 | git_state.read_git_state: no last fetch for a checkout never fetched | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_reports_the_last_fetch_in_utc_once_one_happened | keep | 9 | git_state.read_git_state: the last fetch is reported in UTC | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
test_reports_a_failed_fetch | keep | 9 | git_state.fetch: a failed fetch returns False | cli/tests/test_git_state.py;cli/sushihub/services/git_state.py
```

### `cli/tests/test_gui_build.py`

```
test_gui_root_is_the_application_directory_of_the_workspace | keep | 9 | gui.gui_root: returns the application directory of the workspace | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_gui_root_defaults_to_the_workspace_the_environment_names | keep | 9 | gui.gui_root: defaults to the workspace the environment names | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_gui_root_refuses_a_workspace_without_the_application_sources | split | 3 | gui.gui_root: refuses a workspace without sources with the hub error type, and its hint names the clone; the hint is also tested in the next test, the type is not | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_the_missing_sources_hint_names_the_repository_only_by_its_clone_url | keep | 9 | gui.gui_root: the hint carries the clone URL and no repository word | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_the_compiler_is_left_to_cmake_when_none_is_configured | resize | 8 | GuiConfig.resolved_compiler: empty when no compiler is configured; resolved_compiler does no I/O, so small sees it | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_an_explicit_compiler_still_wins | resize | 8 | GuiConfig.resolved_compiler: an explicit compiler wins; pure, small sees it | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_run_launches_the_application_by_default | rewrite | 1 | gui run target: default target from the profile; a constant check, a forbidden trivial kind; test gui.run's chosen target instead | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_the_configure_points_cmake_at_the_provisioned_vcpkg_tree | keep | 9 | gui.build: configure argv points cmake at the vcpkg tree | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_the_configure_turns_manifest_mode_off_and_tests_on | split | 3 | gui.build: manifest mode off and tests on are two argv promises | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_the_configure_names_the_build_type_and_the_build_directory | split | 3 | gui.build: the build type and the build directory are two argv promises, plus the compile configuration | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_the_configure_names_no_compiler_when_none_is_configured | keep | 9 | gui.build: no CMAKE_CXX_COMPILER is passed when none is configured | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_a_caller_define_comes_after_every_default | keep | 9 | gui.build: a caller define is the last argv entry | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_a_define_without_a_value_is_refused | keep | 9 | gui.build: a define without a value returns 2 and configures nothing | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_clean_removes_the_tree_before_configuring | rewrite | 2 | gui.build with clean: removes the tree before configuring; the test never checks the order, so a clean after configure passes | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_test_passes_the_filter_the_repeat_and_the_jobs_through_with_no_label | keep | 9 | gui.test: passes the filter, repeat and jobs through with no label | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_test_refuses_before_the_first_build | merge | 4 | gui.test: refuses before the first build and names hub gui build; merge with cli/tests/test_gui_build.py::test_run_refuses_before_the_first_build | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_run_refuses_before_the_first_build | merge | 4 | gui.run: refuses before the first build and names hub gui build; merge with cli/tests/test_gui_build.py::test_test_refuses_before_the_first_build | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
test_clean_removes_the_build_directory | keep | 9 | gui.clean: removes the build directory | cli/tests/test_gui_build.py;cli/sushihub/gui_config.py
```

### `cli/tests/test_help_screen.py`

```
test_root_help_lists_the_five_groups_with_the_sub_app_last | keep | 9 | root help: group headings in order with the sub-app last | cli/tests/test_help_screen.py
test_every_command_sits_under_its_own_group[heading] | keep | 9 | root help: each command sits under its own heading | cli/tests/test_help_screen.py
test_no_command_is_listed_under_a_group_it_does_not_belong_to | keep | 9 | root help: no command appears under a heading it does not belong to | cli/tests/test_help_screen.py
test_a_command_help_carries_examples | merge | 4 | command help carries examples; merge with cli/tests/test_help_screen.py::test_a_gui_command_help_carries_examples | cli/tests/test_help_screen.py
test_a_gui_command_help_carries_examples | merge | 4 | command help carries examples; merge with cli/tests/test_help_screen.py::test_a_command_help_carries_examples | cli/tests/test_help_screen.py
```

### `cli/tests/test_hub_install.py`

```
test_names_the_command_and_the_editable_channel | rewrite | 1 | hub_install.read_hub_install: the command and the channel; the command is a literal constant and the frozen channel branch is untested | cli/tests/test_hub_install.py;cli/sushihub/services/hub_install.py
test_reports_no_alias_when_no_rc_file_carries_the_marker | keep | 9 | read_hub_install: no alias when no rc file carries the marker | cli/tests/test_hub_install.py;cli/sushihub/services/hub_install.py
test_finds_the_alias_in_bashrc | merge | 4 | read_hub_install: the alias is found in a profile carrying the marker; merge with test_finds_the_alias_in_the_powershell_profile and test_finds_the_alias_in_the_windows_powershell_profile | cli/tests/test_hub_install.py;cli/sushihub/services/hub_install.py
test_finds_the_alias_in_the_powershell_profile | merge | 4 | read_hub_install: the alias is found in a profile carrying the marker; merge with test_finds_the_alias_in_bashrc and test_finds_the_alias_in_the_windows_powershell_profile | cli/tests/test_hub_install.py;cli/sushihub/services/hub_install.py
test_finds_the_alias_in_the_windows_powershell_profile | merge | 4 | read_hub_install: the alias is found in a profile carrying the marker; merge with test_finds_the_alias_in_bashrc and test_finds_the_alias_in_the_powershell_profile | cli/tests/test_hub_install.py;cli/sushihub/services/hub_install.py
test_the_marker_matches_what_both_installers_write | keep | 9 | hub_install: the marker matches both installers; the oracle is installer text, not the code under test | cli/tests/test_hub_install.py;cli/sushihub/services/hub_install.py
```

### `cli/tests/test_identity.py`

```
test_identity_url_prefers_env | keep | 9 | identity_url: the environment wins over the workspace key | cli/tests/test_identity.py
test_identity_url_reads_the_config_key | keep | 9 | identity_url: the workspace key is read when no environment value is set | cli/tests/test_identity.py
test_identity_url_falls_back_to_the_packaged_defaults | merge | 4 | identity_url: packaged default when the workspace names no url; merge with test_identity_url_answers_outside_any_workspace | cli/tests/test_identity.py
test_identity_url_answers_outside_any_workspace | merge | 4 | identity_url: packaged default outside any workspace; merge with test_identity_url_falls_back_to_the_packaged_defaults | cli/tests/test_identity.py
test_memory_store_round_trips_and_clears | keep | 9 | MemoryStore: save, load and clear round-trip | cli/tests/test_identity.py
test_keyring_store_round_trips_through_the_backend | keep | 9 | KeyringStore: round-trips through the keyring backend, which the test replaces with an in-memory backend restored afterwards | cli/tests/test_identity.py
test_keyring_store_reads_a_corrupt_entry_as_absent | keep | 9 | KeyringStore: a corrupt entry reads as absent | cli/tests/test_identity.py
test_keyring_store_clear_is_quiet_when_nothing_is_stored | keep | 9 | KeyringStore: clear is quiet when nothing is stored | cli/tests/test_identity.py
test_every_keyring_failure_is_a_credential_store_error | keep | 9 | KeyringStore: each failing call raises CredentialStoreError with its cause kept | cli/tests/test_identity.py
test_the_account_errors_share_the_base_the_entry_point_catches | resize | 8 | identity error classes: derive from SushiCoreError; a class relation needs no file, network or process, so small sees it | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_a_refused_connection_is_reported_as_unreachable | resize | 8 | SushiAccount: a URLError becomes AccountUnreachable with its cause; the http seam is injected, no I/O, small sees it | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_a_connect_timeout_is_reported_as_unreachable | resize | 8 | SushiAccount: a connect timeout becomes AccountUnreachable; injected http, small sees it | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_a_read_timeout_is_reported_as_unreachable | resize | 8 | SushiAccount: a read timeout becomes AccountUnreachable with the timeout as cause; injected http, small sees it | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_start_device_login_returns_the_code_and_the_uri | keep | 9 | SushiAccount.start_device_login: the wire answer maps to a DeviceCode; the local fake server is the boundary | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_wait_for_token_polls_until_the_grant_is_approved | split | 3 | SushiAccount.wait_for_token: polls at the granted interval until approved, and returns and stores tokens with an expiry; the parts can break apart | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_slow_down_doubles_the_interval_once | keep | 9 | SushiAccount.wait_for_token: slow_down doubles the interval once | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_wait_for_token_reports_each_poll | keep | 9 | SushiAccount.wait_for_token: each poll is reported | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_access_denied_ends_the_login | merge | 4 | SushiAccount.wait_for_token: a terminal grant error ends the login; merge with test_expired_token_ends_the_login | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_expired_token_ends_the_login | merge | 4 | SushiAccount.wait_for_token: a terminal grant error ends the login; merge with test_access_denied_ends_the_login | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_access_token_is_returned_untouched_while_it_lives | resize | 8 | SushiAccount.access_token: a live token is returned untouched; decision on expiry, injected clock and http, small sees it | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_access_token_refreshes_inside_the_thirty_second_margin | resize | 8 | SushiAccount.access_token: refresh inside the 30 s margin; decision on the margin, small with injected clock and http; the boundary at exactly 30 s is untested | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_a_refused_refresh_clears_the_store | resize | 8 | SushiAccount.access_token: a refused refresh clears the store; decision on values, small with injected http | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_me_is_none_with_an_empty_store | resize | 8 | SushiAccount.me: None with an empty store and no request; decision, small with injected http | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_me_reads_the_account_and_its_licences | keep | 9 | SushiAccount.me: the wire answer maps to Account and Licence values; the fake server is the boundary | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_logout_forgets_the_session | resize | 8 | SushiAccount.logout: clears the store; decision on the store only, small with a MemoryStore | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_licence_token_is_issued_for_a_licensed_product | keep | 9 | SushiAccount.licence_token: the wire answer maps to a LicenceToken and the bearer is sent | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_licence_token_refuses_an_unlicensed_product | keep | 9 | SushiAccount.licence_token: a 403 maps to NoLicence | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_resolve_release_returns_the_url_the_hash_and_the_size | keep | 9 | SushiAccount.resolve_release: returns the release info from the wire | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_resolve_release_carries_the_version_when_one_is_asked_for | keep | 9 | SushiAccount.resolve_release: sends the requested version | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_resolve_release_reports_that_there_is_no_release | keep | 9 | SushiAccount.resolve_release: a 404 maps to NoRelease | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_resolve_release_reports_an_unknown_product | keep | 9 | SushiAccount.resolve_release: an unknown product maps to UnknownProduct | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_a_licence_token_without_a_session_is_refused_before_the_request | resize | 8 | SushiAccount.licence_token: refused before any request when there is no session; decision, small with injected http | cli/tests/test_identity.py;cli/sushihub/services/identity.py
test_login_stores_the_session_and_returns_the_email | rewrite | 1 | session.login: stores the session and returns the email; replaces session.client through _bind | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_login_reports_a_refused_grant | rewrite | 1 | session.login: a refused grant gives exit 1; replaces session.client through _bind | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_logout_command_clears_the_store | delete | 1 | session.logout: clears the store; replaces session.client; the same promise is at CLI level in cli/tests/test_json_streams.py::test_logout_under_json_clears_the_store, which is kept | cli/tests/test_identity.py;cli/tests/test_json_streams.py;cli/sushihub/services/session.py
test_whoami_reports_that_nobody_is_signed_in | rewrite | 1 | session.whoami: nobody signed in gives exit 1; replaces session.client | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_whoami_carries_the_account_as_its_payload | rewrite | 1 | session.whoami: the account is the payload; replaces session.client | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_license_carries_the_licences_alone | rewrite | 1 | session.license: the payload carries the licences alone; replaces session.client | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_license_says_so_when_the_account_holds_none | rewrite | 1 | session.license: an empty licence list is reported; replaces session.client | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_an_account_command_reports_a_failing_credential_store[command] | rewrite | 1 | session logout, whoami and license: a failing credential store prints one error line and gives exit 1; replaces session.client; parametrised over three commands | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_login_reports_a_session_it_could_not_store | rewrite | 1 | session.login: a session that cannot be stored gives one error line and exit 1; replaces session.client | cli/tests/test_identity.py;cli/sushihub/services/session.py
test_whoami_reports_an_unreachable_server | rewrite | 1 | session.whoami: an unreachable server gives one error line; replaces session.client | cli/tests/test_identity.py;cli/sushihub/services/session.py
```

### `cli/tests/test_init.py`

```
test_init_writes_the_marker_directory | rewrite | 1 | init: writes the marker directory and a versioned workspace file; the fixture replaces modules.deps_dir and modules.console | cli/tests/test_init.py;cli/sushihub/services/modules.py
test_init_creates_the_dependency_tree | rewrite | 1 | init: creates the dependency tree; the fixture replaces modules.deps_dir | cli/tests/test_init.py;cli/sushihub/services/modules.py
test_init_writes_every_gitignore_line | rewrite | 1 | init: writes each gitignore line once; reaches the private _GITIGNORE_LINES and replaces modules.deps_dir | cli/tests/test_init.py;cli/sushihub/services/modules.py
test_init_separates_its_lines_from_an_existing_file | rewrite | 1 | init: an existing gitignore without a trailing newline keeps its last line; the fixture replaces modules.deps_dir | cli/tests/test_init.py;cli/sushihub/services/modules.py
test_a_second_init_adds_nothing | rewrite | 1 | init: a second run leaves the gitignore byte-identical and says so; the fixture replaces modules.deps_dir | cli/tests/test_init.py;cli/sushihub/services/modules.py
```

### `cli/tests/test_json_streams.py`

```
test_events_schema_accepts_each_kind | rewrite | 7 | events schema: accepts each event kind; a loop over kinds in the body; rows instead | cli/tests/test_json_streams.py
test_events_schema_rejects_an_unknown_key_and_level | split | 3 | events schema: rejects an unknown level and an unknown key; two promises that can break apart | cli/tests/test_json_streams.py
test_describe_schema_accepts_the_documented_example | keep | 9 | describe schema: accepts the documented example; the schema is an independent oracle | cli/tests/test_json_streams.py
test_set_machine_before_first_print_switches_to_json | resize | 8 | console.set_machine: switching before the first print emits JSON; the test reloads the console module to reset process-wide state, so the seam is a console built per run | cli/tests/test_json_streams.py
test_describe_prints_a_valid_catalogue | keep | 9 | describe --describe output: validates against the schema; survivor of the duplicate in test_describe.py | cli/tests/test_json_streams.py
test_home_under_json_ends_with_a_result_carrying_the_paths | keep | 9 | home --json: ends with a result carrying the workspace path | cli/tests/test_json_streams.py
test_status_under_json_emits_a_table_and_a_result | keep | 9 | status --json: a table then a result carrying the modules | cli/tests/test_json_streams.py
test_every_read_only_command_streams_valid_events[args] | merge | 4 | read-only commands stream schema-valid events ending in one result; merge with cli/tests/test_json_streams.py::test_gui_clean_under_json_streams_valid_events; the loop over events in the body moves into a helper named expect_* | cli/tests/test_json_streams.py
test_gui_clean_under_json_streams_valid_events | merge | 4 | gui clean --json streams schema-valid events; merge with test_every_read_only_command_streams_valid_events as one more row | cli/tests/test_json_streams.py
test_every_sushi_id_command_streams_valid_events[args] | rewrite | 1 | account commands stream schema-valid events; the signed_in fixture replaces session.client and webbrowser.open; the loop in the body | cli/tests/test_json_streams.py;cli/tests/test_identity.py;cli/sushihub/services/session.py
test_login_under_json_reports_each_poll_and_ends_with_the_email | rewrite | 1 | session.login under --json: a progress event per poll, ends with the email; the signed_in fixture replaces session.client | cli/tests/test_json_streams.py;cli/tests/test_identity.py;cli/sushihub/services/session.py
test_whoami_under_json_emits_a_table_and_the_account | rewrite | 1 | session.whoami under --json: a table and the account; the signed_in fixture replaces session.client | cli/tests/test_json_streams.py;cli/sushihub/services/session.py
test_license_under_json_emits_a_table_and_the_licences | rewrite | 1 | session.license under --json: a table and the licences; the signed_in fixture replaces session.client | cli/tests/test_json_streams.py;cli/sushihub/services/session.py
test_logout_under_json_clears_the_store | rewrite | 1 | session.logout under --json: clears the store and ends with an ok result; the signed_in fixture replaces session.client; survivor of the duplicate in test_identity.py | cli/tests/test_json_streams.py;cli/sushihub/services/session.py
```

### `cli/tests/test_link.py`

```
test_the_registry_file_carries_a_modules_table | keep | 9 | links.write: writes a modules table naming the checkout | cli/tests/test_link.py;cli/sushihub/services/links.py
test_entries_are_written_in_name_order | keep | 9 | links.write: entries are written in name order | cli/tests/test_link.py;cli/sushihub/services/links.py
test_relinking_replaces_the_path_rather_than_repeating_it | keep | 9 | links.write: a relink replaces the path | cli/tests/test_link.py;cli/sushihub/services/links.py
test_the_registry_reads_back_what_link_wrote | keep | 9 | links.registered: reads back what write wrote | cli/tests/test_link.py;cli/sushihub/services/links.py
test_link_refuses_sushicore | keep | 9 | modules.link: refuses sushicore with its message and writes nothing | cli/tests/test_link.py;cli/sushihub/services/modules.py
test_link_refuses_a_name_outside_the_catalog | keep | 9 | modules.link: refuses an unknown name with the choices and writes nothing | cli/tests/test_link.py;cli/sushihub/services/modules.py
test_link_refuses_a_path_that_is_not_there | keep | 9 | modules.link: refuses a missing path and writes nothing | cli/tests/test_link.py;cli/sushihub/services/modules.py
test_link_takes_an_alias_and_records_the_full_name | keep | 9 | modules.link: an alias records the full module name | cli/tests/test_link.py;cli/sushihub/services/modules.py
test_a_dry_run_writes_nothing | keep | 9 | modules.link: a dry run reports the link and writes nothing | cli/tests/test_link.py;cli/sushihub/services/modules.py
```

### `cli/tests/test_manifest_precedence.py`

```
test_a_checkout_the_catalog_never_heard_of_is_known | keep | 9 | presence.workspace_modules: a checkout with a manifest and no catalog entry is known | cli/tests/test_manifest_precedence.py;cli/sushihub/services/presence.py
test_the_catalog_still_answers_for_a_checkout_that_says_nothing | merge | 4 | presence.workspace_modules: the catalog prefix survives; subsumed by test_the_catalog_keeps_its_order_and_the_rest_follow_by_name, which checks the same prefix and more | cli/tests/test_manifest_precedence.py;cli/sushihub/services/presence.py
test_the_checkout_wins_when_both_describe_it | keep | 9 | presence.workspace_modules: the checkout's manifest wins over the catalog | cli/tests/test_manifest_precedence.py;cli/sushihub/services/presence.py
test_the_catalog_keeps_its_order_and_the_rest_follow_by_name | keep | 9 | presence.workspace_modules: catalog order first, the rest by name | cli/tests/test_manifest_precedence.py;cli/sushihub/services/presence.py
test_a_linked_checkout_outside_the_root_is_read_too | keep | 9 | presence.workspace_modules: a linked checkout outside the root is read | cli/tests/test_manifest_precedence.py;cli/sushihub/services/presence.py
test_a_manifest_that_will_not_read_is_reported_rather_than_raised | keep | 9 | presence.workspace_modules: a broken manifest is reported, not raised | cli/tests/test_manifest_precedence.py;cli/sushihub/services/presence.py
test_link_accepts_a_checkout_that_describes_itself | rewrite | 1 | modules.link: accepts a checkout describing itself; replaces links.registered, links.write and the private _install_module_cli | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_refuses_a_checkout_that_describes_a_different_module | rewrite | 1 | modules.link: refuses a checkout describing another module; replaces links.registered and links.write | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_refuses_a_catalog_name_for_a_checkout_that_describes_another_module | rewrite | 1 | modules.link: a catalog name does not excuse a checkout describing another module; replaces links.registered, links.write and _install_module_cli through _link_spy; merge with the alias test once the spy is gone | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_refuses_an_alias_for_a_checkout_that_describes_another_module | rewrite | 1 | modules.link: an alias does not excuse a checkout describing another module; replaces links.registered, links.write and _install_module_cli through _link_spy; merge with the catalog-name test once the spy is gone | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_accepts_a_catalog_name_when_the_checkout_agrees | rewrite | 1 | modules.link: a catalog name with an agreeing manifest links; replaces links.registered, links.write and _install_module_cli | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_reports_an_unreadable_manifest_under_a_catalog_name | rewrite | 1 | modules.link: an unreadable manifest under a catalog name stops the link; replaces links.registered, links.write and _install_module_cli through _link_spy; merge with the next test once the spy is gone | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_reports_a_manifest_that_will_not_read | delete | 1 | modules.link: an unreadable manifest stops the link; replaces links.registered; the same promise is in test_link_reports_an_unreadable_manifest_under_a_catalog_name, which is kept and rewritten | cli/tests/test_manifest_precedence.py;cli/sushihub/services/modules.py
test_link_still_refuses_a_checkout_that_says_nothing | delete | 1 | modules.link: an unknown name with no manifest is refused; replaces links.registered; the same promise is in cli/tests/test_link.py::test_link_refuses_a_name_outside_the_catalog, which keeps it | cli/tests/test_manifest_precedence.py;cli/tests/test_link.py;cli/sushihub/services/modules.py
```

### `cli/tests/test_migrate_command.py`

```
test_dry_run_prints_every_component_and_changes_nothing | split | 3 | migrate dry run: prints each component and the space, and changes nothing; two promises joined by and | cli/tests/test_migrate_command.py
test_run_with_yes_links_the_old_path_and_writes_the_registry | split | 3 | migrate run: links the old path and writes the registry; two promises that can break apart | cli/tests/test_migrate_command.py
test_run_asks_before_moving_and_stops_on_no | keep | 9 | migrate run: a no at the prompt stops the move | cli/tests/test_migrate_command.py
test_run_to_the_default_root_leaves_the_variable_unset | keep | 9 | migrate run to the default root: leaves the variable unset | cli/tests/test_migrate_command.py
test_run_to_another_path_sets_the_variable_and_says_so | split | 3 | migrate run to another path: sets the variable, and prints the facts of the move; the parts can break apart | cli/tests/test_migrate_command.py
test_run_rewrites_the_tool_paths_of_the_workspace_file | keep | 9 | migrate run: rewrites the tool paths to the new root | cli/tests/test_migrate_command.py
test_run_journals_the_earlier_variable_and_the_workspace_rewrite | split | 3 | migrate journal: the earlier variable and the workspace step are two entries that can break apart | cli/tests/test_migrate_command.py
test_a_second_run_reports_the_finished_move | keep | 9 | migrate: a second run reports the finished move and changes nothing | cli/tests/test_migrate_command.py
test_run_refuses_a_target_that_holds_a_component | keep | 9 | migrate run: refuses a target that holds a component | cli/tests/test_migrate_command.py
test_rollback_restores_the_tree_the_file_and_the_variable | split | 3 | migrate rollback: restores the tree, the workspace file and the variable; each can break apart | cli/tests/test_migrate_command.py
test_rollback_removes_a_variable_that_was_not_set_before | keep | 9 | migrate rollback: unsets a variable the migration set | cli/tests/test_migrate_command.py
test_rollback_with_nothing_to_undo_exits_zero | keep | 9 | migrate rollback: nothing to undo exits 0 and changes nothing | cli/tests/test_migrate_command.py
test_finalize_deletes_the_old_copy_and_keeps_the_link | split | 3 | migrate finalize: deletes the old copy and keeps the link, and rollback still works after it; three parts that can break apart | cli/tests/test_migrate_command.py
test_finalize_before_a_migration_refuses | keep | 9 | migrate finalize: refuses before a migration and deletes nothing | cli/tests/test_migrate_command.py
test_finalize_with_drop_link_removes_the_link | keep | 9 | migrate finalize --drop-link: removes the link | cli/tests/test_migrate_command.py
test_drop_link_is_refused_when_nothing_else_names_the_tree | keep | 9 | migrate finalize --drop-link: refused when the variable does not name the tree | cli/tests/test_migrate_command.py
test_deps_dir_is_the_workspace_tree_before_a_migration | delete | 4 | config.deps_dir: the workspace tree before a migration; same promise as cli/tests/test_workspace_resolution.py::test_dependencies_default_to_one_tree_under_the_root | cli/tests/test_migrate_command.py;cli/tests/test_workspace_resolution.py
test_deps_dir_follows_the_link_after_a_migration | keep | 9 | config.deps_dir: follows the link after a migration and the old tree after rollback | cli/tests/test_migrate_command.py
test_deps_dir_prefers_sushisystems_home_to_the_workspace | keep | 9 | config.deps_dir: the environment variable wins over the workspace | cli/tests/test_migrate_command.py
test_deps_dir_prefers_the_legacy_override_to_everything | merge | 4 | config.deps_dir: the legacy override wins over every other source; merge with cli/tests/test_workspace_resolution.py::test_the_dependency_override_wins; this copy adds the new variable | cli/tests/test_migrate_command.py;cli/tests/test_workspace_resolution.py
test_deps_dir_falls_back_to_a_user_path_outside_a_workspace | delete | 1 | config.deps_dir: user path outside a workspace; replaces config.find_workspace_root; same promise as cli/tests/test_workspace_resolution.py::test_dependencies_fall_back_to_a_user_path_outside_a_workspace | cli/tests/test_migrate_command.py;cli/tests/test_workspace_resolution.py
test_the_command_runs_a_dry_run_through_typer | keep | 9 | migrate command: a dry run through Typer exits 0 and leaves the tree | cli/tests/test_migrate_command.py
test_the_command_refuses_rollback_with_finalize | keep | 9 | migrate command: --rollback with --finalize is a usage error | cli/tests/test_migrate_command.py
test_the_command_refuses_drop_link_without_finalize | keep | 9 | migrate command: --drop-link without --finalize is a usage error | cli/tests/test_migrate_command.py
test_the_command_migrates_and_rolls_back_through_typer | keep | 9 | migrate command: a migration followed by --rollback restores the workspace; a round trip is one promise | cli/tests/test_migrate_command.py
```

### `cli/tests/test_module_fragments.py`

```
test_a_manifest_names_the_fragment | keep | 9 | module_fragments.fragment_of: the manifest's fragment key wins | cli/tests/test_module_fragments.py;cli/sushihub/services/module_fragments.py
test_without_a_manifest_the_catalog_path_is_used | keep | 9 | module_fragments.fragment_of: without a manifest the catalog path applies | cli/tests/test_module_fragments.py;cli/sushihub/services/module_fragments.py
test_workspace_pins_yields_each_module_and_its_pin | rewrite | 1 | module_fragments.workspace_pins: yields each module, fragment and pin; replaces module_fragments.present_modules | cli/tests/test_module_fragments.py;cli/sushihub/services/module_fragments.py
```

### `cli/tests/test_module_manifest.py`

```
test_a_complete_manifest_reads_into_a_module | resize | 8 | module_manifest.read: a complete manifest reads into a module; decision on parsed values, the file is the only door, seam needed | cli/tests/test_module_manifest.py
test_the_optional_keys_have_the_conventional_answers | resize | 8 | module_manifest.read: optional keys take their conventional values; decision on values, seam needed | cli/tests/test_module_manifest.py
test_a_checkout_without_a_manifest_answers_none | keep | 9 | module_manifest.read: no manifest answers None; the absent file is the boundary | cli/tests/test_module_manifest.py
test_a_missing_required_key_names_itself | resize | 8 | module_manifest.read: a missing required key is named in the error; decision on values, seam needed | cli/tests/test_module_manifest.py
test_a_name_that_disagrees_with_the_directory_is_refused | resize | 8 | module_manifest.read: a name that disagrees with the directory is refused; decision on values, seam needed | cli/tests/test_module_manifest.py
test_an_unknown_key_is_ignored | resize | 8 | module_manifest.read: an unknown key is ignored; decision on values, seam needed | cli/tests/test_module_manifest.py
test_an_unknown_table_is_refused | resize | 8 | module_manifest.read: an unknown table is refused; decision on values, seam needed | cli/tests/test_module_manifest.py
test_a_file_without_the_module_table_is_refused | resize | 8 | module_manifest.read: a file without the module table is refused; decision on values, seam needed | cli/tests/test_module_manifest.py
```

### `cli/tests/test_pins.py`

```
test_rewrite_changes_only_the_two_keys_of_the_table | resize | 8 | pins.rewrite_pin, only two keys change; pure text in a medium-marked file, small holds | cli/tests/test_pins.py; cli/sushihub/services/pins.py
test_rewrite_renames_every_deprecated_table | resize | 8 | pins.rewrite_pin, deprecated headers renamed; pure text, small holds | cli/tests/test_pins.py; cli/sushihub/services/pins.py
test_a_fragment_without_the_table_is_refused | resize | 8 | pins.rewrite_pin raises ValueError; pure text, small holds | cli/tests/test_pins.py; cli/sushihub/services/pins.py
test_move_pin_rewrites_every_module_that_pins_the_library | rewrite | 1 | two_modules fixture replaces module_fragments.present_modules, a repository function that workspace_pins calls; the test writes no real workspace | cli/tests/test_pins.py; cli/sushihub/services/pins.py; cli/sushihub/services/module_fragments.py
test_a_dry_run_writes_nothing | rewrite | 1 | same two_modules fixture replaces present_modules; the test also joins a return count and a file check (split pending) | cli/tests/test_pins.py; cli/sushihub/services/pins.py; cli/sushihub/services/module_fragments.py
test_pin_refuses_a_short_commit | rewrite | 1 | replaces pins.workspace_root, a repository function; set SUSHISTACK_HOME to tmp_path instead | cli/tests/test_pins.py; cli/sushihub/services/pins.py; cli/tests/conftest.py
test_pin_reads_the_commit_from_the_tag_when_none_is_given | rewrite | 1 | replaces pins.tag_commit and pins.workspace_root, both repository functions; the git call is the seam and needs its own adapter test | cli/tests/test_pins.py; cli/sushihub/services/pins.py; cli/tests/conftest.py
test_pin_fails_when_the_tag_is_not_found | rewrite | 1 | replaces pins.tag_commit and pins.workspace_root, both repository functions | cli/tests/test_pins.py; cli/sushihub/services/pins.py; cli/tests/conftest.py
```

### `cli/tests/test_presence.py`

```
test_the_manifest_name_is_the_one_sushicore_looks_for | rewrite | 1 | trivial constant equality; the cross-unit promise is only stated here; check read_release against the manifest name sushicore's own profile writes | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_read_release_reads_product_version_and_platform | resize | 8 | presence.read_release, decision on parsed values reached only through a file; the parse needs a seam split from the file read | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_read_release_is_none_without_a_manifest | merge | 4 | same promise as the not-JSON and missing-field tests (None for an invalid release), other inputs; merge into rows with test_read_release_is_none_when_the_manifest_is_not_json | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_read_release_is_none_when_the_manifest_is_not_json | merge | 4 | same promise as test_read_release_is_none_without_a_manifest, other input; merge into rows with test_read_release_is_none_without_a_manifest | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_read_release_is_none_when_a_field_is_missing | merge | 4 | same promise as test_read_release_is_none_without_a_manifest, other input; merge into rows with test_read_release_is_none_without_a_manifest | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_module_dir_follows_the_catalog_directory | resize | 8 | presence.module_dir decides on values; a Path is enough, no directory is needed; small | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_module_dir_prefers_a_link_over_the_catalog | resize | 8 | presence.module_dir, link precedence on values; small | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_module_dir_falls_back_to_the_bare_name_for_a_stale_link | rewrite | 7 | name says stale link; body passes no link map, so the promise is the unknown-name fallback; rename | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_a_directory_with_the_manifest_is_binary | keep | 9 | presence.presence_of, binary when the manifest is present; the directory state is the boundary, medium holds | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_a_directory_with_git_is_cloned | keep | 9 | presence.presence_of, cloned when .git is present | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_a_directory_that_is_not_there_is_absent | keep | 9 | presence.presence_of, absent when nothing is there | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_a_linked_checkout_is_linked | keep | 9 | presence.presence_of, linked for a link to a checkout | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_a_linked_path_without_a_checkout_is_absent | keep | 9 | presence.presence_of, absent for a link to nothing; a different branch from the plain absence test | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_describe_names_the_version_of_a_binary_install | keep | 9 | presence.describe, binary with version | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_describe_falls_back_to_the_bare_form_for_a_broken_manifest | keep | 9 | presence.describe, bare form for a broken manifest | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_describe_gives_the_directory_for_a_clone_and_an_absence | split | 3 | "and" joins the clone outcome and the absence outcome | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_describe_gives_the_path_for_a_link_and_says_when_it_is_gone | split | 3 | "and" joins the link path and the missing-link text | cli/tests/test_presence.py; cli/sushihub/services/presence.py
test_status_rows_carry_the_presence_and_the_version | rewrite | 1 | workspace() helper replaces pipx.installed, a repository function; the test also builds a dict comprehension in its body | cli/tests/test_presence.py; cli/sushihub/services/pipx.py
test_update_refreshes_a_binary_module_through_sushi_id | rewrite | 1 | workspace() replaces pipx.installed; git_ops.run and binary.update are replaced, all repository functions; the name mentions sushi id and the body does not check it | cli/tests/test_presence.py; cli/sushihub/services/pipx.py
test_readiness_says_a_binary_module_has_nothing_to_build | rewrite | 1 | workspace() replaces pipx.installed, a repository function | cli/tests/test_presence.py; cli/sushihub/services/pipx.py
test_a_binary_module_contributes_no_dependency_fragment | rewrite | 1 | workspace() replaces pipx.installed; the test has a for loop in its body | cli/tests/test_presence.py; cli/sushihub/services/pipx.py
```

### `cli/tests/test_releases.py`

```
test_host_platform_names_windows_x64 | merge | 4 | releases.host_platform, same mapping promise as the Linux and pass-through tests with other inputs; the stdlib platform functions are replaced, which is allowed | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_host_platform_names_linux_x64 | merge | 4 | same promise as the Windows test; merge into rows with test_host_platform_names_windows_x64 | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_host_platform_passes_a_machine_it_does_not_rename_through | merge | 4 | same promise, the pass-through input; merge into rows with test_host_platform_names_windows_x64 | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_download_writes_the_file_and_reports_each_chunk | keep | 9 | releases.download, bytes written and progress per chunk; file write is the boundary, medium holds | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_download_reports_no_total_when_the_response_declares_none | keep | 9 | releases.download, zero total when none declared; a different promise | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_verify_accepts_the_declared_size_and_digest | keep | 9 | releases.verify, a matching size and digest pass; file hashing is the boundary | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_verify_names_the_size_when_it_differs | keep | 9 | releases.verify, size mismatch named | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_verify_names_the_digest_when_it_differs | keep | 9 | releases.verify, digest mismatch named | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_unpack_extracts_a_zip | merge | 4 | releases.unpack, same extraction promise as the tar.gz test with another format; merge into rows with test_unpack_extracts_a_tar_gz | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_unpack_extracts_a_tar_gz | merge | 4 | same promise as the zip test; merge into rows with test_unpack_extracts_a_zip | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_unpack_refuses_a_member_that_escapes_the_directory | merge | 4 | same promise as the tar escape test; merge into rows with test_unpack_refuses_a_tar_member_that_escapes_the_directory | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_unpack_refuses_a_tar_member_that_escapes_the_directory | merge | 4 | same promise as the zip escape test; merge into rows with test_unpack_refuses_a_member_that_escapes_the_directory | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_unpack_refuses_an_archive_without_a_manifest_at_the_top | keep | 9 | releases.unpack, refusal without a top-level manifest | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_unpack_refuses_a_suffix_it_does_not_know | keep | 9 | releases.unpack, unknown suffix refused and named | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_install_release_unpacks_it_and_returns_the_manifest | split | 3 | "and" joins the unpack and manifest return with the staging check (nothing left beside root) | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_install_release_reports_the_download_as_progress | keep | 9 | releases.install_release, progress events from the download | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_install_release_asks_for_this_machines_platform | rewrite | 1 | replaces releases.host_platform, a repository function; patch the stdlib platform functions instead | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_install_release_keeps_the_old_install_when_the_hash_does_not_match | keep | 9 | releases.install_release, the old install survives a mismatch; one outcome | cli/tests/test_releases.py; cli/sushihub/services/releases.py
test_install_release_replaces_an_older_install | keep | 9 | releases.install_release, older install replaced; one outcome | cli/tests/test_releases.py; cli/sushihub/services/releases.py
```

### `cli/tests/test_selection.py`

```
test_empty_workspace_selects_no_toolchain_but_keeps_the_gpu_on | keep | 9 | selection.derived_selection, one value; sushicore probe is replaced, and it is not a repository function | cli/tests/test_selection.py; cli/sushihub/setup/factory.py; cli/tests/conftest.py
test_a_bare_install_selects_one_sycl_toolchain | keep | 9 | selection.derived_selection, one toolchain for a bare install | cli/tests/test_selection.py; cli/sushihub/setup/factory.py; cli/tests/conftest.py
test_a_present_toolchain_selects_no_download | keep | 9 | selection.derived_selection, a present toolchain selects no download | cli/tests/test_selection.py; cli/sushihub/setup/factory.py; cli/tests/conftest.py
test_a_shared_fragment_cannot_select_a_toolchain | keep | 9 | selection.derived_selection, a shared fragment selects none | cli/tests/test_selection.py; cli/sushihub/setup/factory.py; cli/tests/conftest.py
test_the_base_fragment_comes_from_sushicore | resize | 8 | selection.manifest_sources enumerates shipped manifest files on disk (dependency_source.py, manifest_sources loop); medium is the smallest size | cli/tests/test_selection.py; cli/sushihub/setup/dependency_source.py
test_merged_applies_known_keys_only | keep | 9 | ToolchainSelection.merged, unknown keys ignored | cli/tests/test_selection.py
test_build_pipeline_defaults_to_the_derived_selection | rewrite | 1 | build_pipeline calls workspace_root(), which reads the environment and the file system; forbidden in a small test, and the only test of this promise | cli/tests/test_selection.py; cli/sushihub/setup/factory.py
test_build_pipeline_merges_an_explicit_selection_over_the_derived_one | rewrite | 1 | build_pipeline reaches workspace_root() in a small test; only test of the explicit merge | cli/tests/test_selection.py; cli/sushihub/setup/factory.py
test_a_shipped_fragment_is_owned_by_the_name_in_its_filename | rewrite | 1 | imports the private _owner_for_shipped, a _private name; the only test of the filename owner; test through manifest_sources' owner pairs | cli/tests/test_selection.py; cli/sushihub/setup/dependency_source.py
test_build_pipeline_honours_the_gpu_turned_off_in_customize | rewrite | 1 | build_pipeline reaches workspace_root() in a small test | cli/tests/test_selection.py; cli/sushihub/setup/factory.py
test_build_pipeline_knows_no_step_that_builds_a_module | rewrite | 1 | build_pipeline builds the workspace sink before it raises ValueError; the environment is reached in a small test | cli/tests/test_selection.py; cli/sushihub/setup/factory.py
test_every_named_step_builds_a_pipeline | rewrite | 1 | for loop in the body; build_pipeline reaches workspace_root() in a small test | cli/tests/test_selection.py; cli/sushihub/setup/factory.py
```

### `cli/tests/test_self_update.py`

```
test_an_index_install_is_upgraded_with_pipx | rewrite | 1 | calls the private modules._self_update, and the calls fixture replaces pipx.installed, pipx.upgrade and git_ops.run, all repository functions; the public entry is modules.sync | cli/tests/test_self_update.py; cli/sushihub/services/modules.py
test_an_editable_install_pulls_its_own_checkout | rewrite | 1 | same private call and the same replaced repository functions | cli/tests/test_self_update.py; cli/sushihub/services/modules.py
test_neither_branch_runs_under_dry_run | rewrite | 1 | same private call and replaced repository functions; two calls in one test | cli/tests/test_self_update.py; cli/sushihub/services/modules.py
test_a_workspace_that_is_no_checkout_is_left_alone | rewrite | 1 | same private call and replaced repository functions | cli/tests/test_self_update.py; cli/sushihub/services/modules.py
test_an_editable_install_outside_a_checkout_warns | rewrite | 1 | same private call and replaced repository functions | cli/tests/test_self_update.py; cli/sushihub/services/modules.py
test_a_failed_upgrade_warns_rather_than_raising | rewrite | 1 | same private call; replaces pipx.installed and pipx.upgrade, repository functions | cli/tests/test_self_update.py; cli/sushihub/services/modules.py
```

### `cli/tests/test_status_payload.py`

```
test_the_offline_payload_matches_the_schema | rewrite | 1 | workspace() helper replaces pipx.installed, a repository function | cli/tests/test_status_payload.py; cli/tests/test_presence.py
test_the_module_list_carries_the_catalog_and_nothing_else | rewrite | 1 | workspace() replaces pipx.installed; a list comprehension in the body | cli/tests/test_status_payload.py; cli/tests/test_presence.py
test_a_checkout_row_carries_its_branch_and_no_binary | rewrite | 1 | workspace() replaces pipx.installed; a dict comprehension in the body; the name joins two facts | cli/tests/test_status_payload.py; cli/tests/test_presence.py
test_a_binary_row_carries_its_platform_and_licence_expiry | rewrite | 1 | workspace() replaces pipx.installed; a generator in the body | cli/tests/test_status_payload.py; cli/tests/test_presence.py
test_the_hub_block_reports_the_alias_under_the_given_home | rewrite | 1 | workspace() replaces pipx.installed | cli/tests/test_status_payload.py; cli/tests/test_presence.py
test_checking_updates_fills_the_latest_release | rewrite | 1 | workspace() replaces pipx.installed; the fake_id server is medium and fine | cli/tests/test_status_payload.py; cli/tests/test_presence.py; cli/tests/test_identity.py
test_a_refused_check_leaves_null_and_one_warning | rewrite | 1 | workspace() replaces pipx.installed; the name joins two outcomes | cli/tests/test_status_payload.py; cli/tests/test_presence.py
```

### `cli/tests/test_theme_tokens.py`

```
test_scanner_reads_plain_and_fstring_constants | rewrite | 1 | list comprehension in the body; the only test of the scanner's reading of constants | cli/tests/test_theme_tokens.py
test_scanner_passes_theme_tokens_and_bare_bold | keep | 9 | the scanner passes theme tokens and bare bold; no loop, no file | cli/tests/test_theme_tokens.py
test_source_names_no_raw_rich_colour | rewrite | 1 | nested comprehension in the body; the test reads every source file under sushihub in a small test | cli/tests/test_theme_tokens.py
```

### `cli/tests/test_tool_paths.py`

```
test_values_under_the_old_root_move_to_the_new_root | resize | 8 | tool_paths, decision on values reached through a workspace file; the path move needs a seam below the file | cli/tests/test_tool_paths.py; cli/sushihub/services/tool_paths.py
test_a_value_equal_to_the_old_root_moves | merge | 4 | same promise (values under the old root move), other input; merge into rows with test_values_under_the_old_root_move_to_the_new_root | cli/tests/test_tool_paths.py; cli/sushihub/services/tool_paths.py
test_a_sibling_folder_with_a_longer_name_is_left_alone | resize | 8 | tool_paths, prefix decision on values reached through a file; seam as for the first test | cli/tests/test_tool_paths.py; cli/sushihub/services/tool_paths.py
test_other_tables_are_written_back_unchanged | keep | 9 | tool_paths, other tables survive the rewrite; file write is the boundary | cli/tests/test_tool_paths.py; cli/sushihub/services/tool_paths.py
test_a_rewrite_back_restores_the_file | keep | 9 | tool_paths, a round trip restores the bytes; metamorphic oracle | cli/tests/test_tool_paths.py; cli/sushihub/services/tool_paths.py
test_a_missing_file_is_not_created | keep | 9 | tool_paths, no file created for a missing workspace file | cli/tests/test_tool_paths.py; cli/sushihub/services/tool_paths.py
```

### `cli/tests/test_update_check.py`

```
test_names_the_latest_release_without_asking_for_a_version | rewrite | 1 | fake_id starts a server thread and a socket in a small test; the only test of the no-version request | cli/tests/test_update_check.py; cli/tests/test_identity.py; cli/sushihub/services/update_check.py
test_gives_the_reason_when_nobody_is_signed_in | rewrite | 1 | fake_id fixture starts a server thread in a small test; the URL is only passed to the client | cli/tests/test_update_check.py; cli/tests/test_identity.py; cli/sushihub/services/update_check.py
test_gives_the_reason_when_the_account_holds_no_licence | rewrite | 1 | fake_id thread in a small test; server state set | cli/tests/test_update_check.py; cli/tests/test_identity.py; cli/sushihub/services/update_check.py
test_gives_the_reason_when_sushi_id_is_unreachable | rewrite | 1 | real socket to 127.0.0.1:9 in a small test; port 9 is an environment assumption | cli/tests/test_update_check.py; cli/sushihub/services/update_check.py; cli/sushihub/services/identity.py
```

### `cli/tests/test_workspace_resolution.py`

```
test_the_environment_variable_names_the_workspace | keep | 9 | config.workspace_root, SUSHISTACK_HOME wins; tmp_path needs medium | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_the_marker_is_found_by_walking_up | keep | 9 | config.workspace_root, walk-up to a marker directory | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_the_old_marker_file_still_resolves | keep | 9 | config.workspace_root, a marker file resolves | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_the_manifests_tree_no_longer_marks_a_workspace | keep | 9 | config.workspace_root, a manifests tree is no marker | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_no_marker_anywhere_is_an_error_the_entry_point_reports | rewrite | 7 | name says the entry point reports the error; the body calls workspace_root only; rename to the error it checks | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_find_workspace_root_answers_none_outside_a_workspace | keep | 9 | config.find_workspace_root, None outside a workspace | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_find_workspace_root_finds_the_marker | rewrite | 6 | oracle is workspace_root, the sibling function under test; compare with unpinned.resolve() | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_the_workspace_file_sits_inside_the_marker_directory | keep | 9 | config.workspace_file, path layout as specified | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_the_defaults_come_from_the_package_not_the_workspace | keep | 9 | config.packaged_defaults, file shipped with the package | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_dependencies_default_to_one_tree_under_the_root | keep | 9 | config.deps_dir, default under the root | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_the_dependency_override_wins | keep | 9 | config.deps_dir, override wins | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
test_dependencies_fall_back_to_a_user_path_outside_a_workspace | keep | 9 | config.deps_dir, per-user fallback | cli/tests/test_workspace_resolution.py; cli/sushihub/config.py
```

### `cli/tests/test_workspace_upgrade.py`

```
test_the_marker_file_becomes_a_directory | keep | 9 | config.upgrade_workspace, marker file becomes a directory | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
test_both_tables_move_across | keep | 9 | config.upgrade_workspace, modules and tool tables move | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
test_the_originals_are_left_alone | keep | 9 | config.upgrade_workspace, originals kept | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
test_upgrading_twice_changes_nothing | keep | 9 | config.upgrade_workspace, idempotent | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
test_a_workspace_with_no_old_data_still_upgrades | keep | 9 | config.upgrade_workspace, version alone | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
test_a_link_written_after_an_upgrade_keeps_the_tool_paths | keep | 9 | links.write keeps the tool table written by the upgrade | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py; cli/sushihub/services/links.py
test_hub_remove_empties_the_tool_table_and_keeps_the_registry | split | 3 | "and" joins the cleared tool table and the kept registry, two outcomes of one call | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
test_a_dry_run_of_hub_remove_leaves_the_tool_table | keep | 9 | UninstallStep dry run writes nothing | cli/tests/test_workspace_upgrade.py; cli/sushihub/config.py
```

### `gui/tests/bridge_test.cpp`

```
LineQueueTest.PopsInPushOrderAndReportsClosure | split | 3 | "And" joins FIFO order and closure reporting; each can break alone | gui/tests/bridge_test.cpp; gui/tests/CMakeLists.txt; gui/src/bridge/Process.cpp (grep)
ProcessTest.ReadsTwoLinesAndExitsZero | rewrite | 1 | drain_until_closed sleeps 1 ms per poll to wait for the child, a sleep to synchronise; the only test of stdout lines | gui/tests/bridge_test.cpp; gui/tests/CMakeLists.txt; gui/src/bridge/Process.cpp (grep)
ProcessTest.EchoesALineWrittenToStandardInput | rewrite | 1 | same sleep poll; the only test of the stdin write | gui/tests/bridge_test.cpp; gui/tests/CMakeLists.txt; gui/src/bridge/Process.cpp (grep)
ProcessTest.ReportsFailureForAProgramThatIsNotThere | resize | 8 | a spawn attempt is an OS boundary, medium is the smallest size; the suite has no Medium_ label | gui/tests/bridge_test.cpp; gui/tests/CMakeLists.txt
```

### `gui/tests/catalogue_test.cpp`

```
CatalogueTest.ReadsTheProgramVersionAndContract | resize | 8 | parse of recorded text read from a fixture file in a small suite; the text can be held in the test | gui/tests/catalogue_test.cpp; gui/tests/FixtureFile.hpp; gui/tests/CMakeLists.txt
CatalogueTest.MapsEveryParameterTypeTheContractAllows | rewrite | 1 | for loop over the type names in the body; the only test of the name-to-type map | gui/tests/catalogue_test.cpp
CatalogueTest.TheHandWrittenCatalogueCarriesEveryParameterType | delete | 1 | nested loops in the body; checks that the fixture covers every type, a property of test data; the type mapping is tested by MapsEveryParameterTypeTheContractAllows | gui/tests/catalogue_test.cpp
CatalogueTest.ReadsAnArgumentAndAnOptionOfTheSameCommand | split | 3 | an argument's fields and an option's fields are two promises, joined by "And" | gui/tests/catalogue_test.cpp
CatalogueTest.ReadsAChoiceWithItsValuesAndLeavesOthersEmpty | split | 3 | choice values and default are one promise; the empty fields of other parameters are a second, joined by "And" | gui/tests/catalogue_test.cpp
CatalogueTest.ReadsACommandWithNoParameters | resize | 8 | parse of recorded text from a fixture file; small suite; no label | gui/tests/catalogue_test.cpp; gui/tests/FixtureFile.hpp
CatalogueTest.TheRecordedCatalogueOffersTheUpdateCheck | resize | 8 | parse of recorded text from a fixture file; small suite; no label | gui/tests/catalogue_test.cpp; gui/tests/FixtureFile.hpp
CatalogueTest.RefusesABadCatalogueWithAReasonInsteadOfThrowing | rewrite | 1 | for loop over a literal list of bad documents in the body, not a row table | gui/tests/catalogue_test.cpp
```

### `gui/tests/event_test.cpp`

```
EventTest.EveryRecordedLineParses | rewrite | 1 | nested loops over files and lines in the body; the only test that every recorded line parses | gui/tests/event_test.cpp; gui/tests/FixtureFile.hpp
EventTest.EveryHandWrittenLineParsesAndTheEightKindsAppear | delete | 1 | loop in the body; the parse-all promise is tested by ScriptedRun.FoldsTheHandWrittenStreamIntoEveryProjection, and the eight-kinds check is fixture coverage | gui/tests/event_test.cpp; gui/tests/model_test.cpp
EventTest.ReadsATableWithItsColumnsAndRows | resize | 8 | pure string parse of a table event; no label | gui/tests/event_test.cpp
EventTest.ReadsAProgressFractionAndItsAbsence | split | 3 | "And" joins a present fraction and an absent one | gui/tests/event_test.cpp
EventTest.ReadsAPromptDefaultAndItsAbsence | split | 3 | "And" joins a present default and an absent one | gui/tests/event_test.cpp
EventTest.ReadsAResultPayloadAsAnObject | resize | 8 | pure string parse of a result event; no label | gui/tests/event_test.cpp
EventTest.RefusesABadLineWithAReasonInsteadOfThrowing | rewrite | 1 | for loop over a literal list of bad lines in the body, not a row table | gui/tests/event_test.cpp
EventTest.RefusesAnEmptyLine | merge | 4 | same refusal promise as RefusesABadLineWithAReasonInsteadOfThrowing, other input; merge into its rows | gui/tests/event_test.cpp
```

### `gui/tests/install_facts_test.cpp`

```
InstallFactsTest.TheRecordedPayloadCarriesTheEngineAndTheHubBlock | split | 3 | recorded payload shape (a fixture check) and find_module and text lookups are two promises, joined by "And" | gui/tests/install_facts_test.cpp; gui/tests/FixtureFile.hpp
InstallFactsTest.WritesTheDistanceOrThatThereIsNoUpstream | resize | 8 | distance text, two inputs of one promise; pure; no label | gui/tests/install_facts_test.cpp
InstallFactsTest.CountsTheLastFetchInWholeDays | resize | 8 | last_fetch text, boundary inputs; pure; no label | gui/tests/install_facts_test.cpp
InstallFactsTest.CountsDaysAcrossALeapDay | split | 3 | leap-day count, epoch zero and invalid input are three promises | gui/tests/install_facts_test.cpp
InstallFactsTest.SaysWhetherANewerReleaseExistsOnlyAfterACheck | resize | 8 | newer_release text across four states; pure; no label | gui/tests/install_facts_test.cpp
InstallFactsTest.ReadsTheLicenceExpiryAsADate | resize | 8 | licence text; pure; no label | gui/tests/install_facts_test.cpp
InstallFactsTest.NamesTheAliasAndTheHubsCurrency | split | 3 | "And" joins the alias text and the hub currency text | gui/tests/install_facts_test.cpp
```

### `gui/tests/model_test.cpp`

```
ScriptedRun.FoldsTheHandWrittenStreamIntoEveryProjection | rewrite | 1 | for loop over fixture lines in the body; file read in the test; the only test that folds every kind | gui/tests/model_test.cpp; gui/tests/FixtureFile.hpp; gui/src/model/CommandRun.cpp
ScriptedRun.FoldsInStagesAndOnlyFinishesWhenTheQueueCloses | split | 3 | "And" joins staged folding and finish-at-close; several actions in the body | gui/tests/model_test.cpp; gui/src/model/CommandRun.cpp
ScriptedRun.KeepsTheLatestProgressAndTheLatestPrompt | split | 3 | "And" joins the latest progress and the latest prompt | gui/tests/model_test.cpp; gui/src/model/CommandRun.cpp
ScriptedRun.RecordsABadLineAsAnErrorAndKeepsFolding | split | 3 | "And" joins the error record and the folding that continues | gui/tests/model_test.cpp; gui/src/model/CommandRun.cpp
ScriptedRun.ClearsThePendingPromptWhenItIsAnswered | resize | 8 | answer clears the pending prompt; spawns nothing; no label | gui/tests/model_test.cpp; gui/src/model/CommandRun.cpp
ScriptedRun.RefusesASecondStart | resize | 8 | second start refused; spawns nothing; no label | gui/tests/model_test.cpp; gui/src/model/CommandRun.cpp
CommandRunTest.ReportsAProgramThatCannotBeSpawned | resize | 8 | spawn of a missing program is an OS boundary, medium holds; the suite has no Medium_ label | gui/tests/model_test.cpp; gui/src/model/CommandRun.cpp
RunLogTest.HoldsNoRunBeforeTheFirstAdoption | resize | 8 | empty RunLog; pure; no label | gui/tests/model_test.cpp
RunLogTest.PointsAtTheRunItAdoptedAndKeepsItsLabel | split | 3 | "And" joins the adopted-run pointer and the kept label | gui/tests/model_test.cpp
RunLogTest.FollowsTheRunAdoptedLast | resize | 8 | RunLog follows the last adopted run; pure; no label | gui/tests/model_test.cpp
```

## Adds

Promises a header or a port states that no test checks: `unit: promise | oracle | size`.

```
modules.add: a linked module is skipped with its link path named and its CLI installed | printed message and install spy | medium
modules.add: a failed clone is reported and the exit code is 1 | exit code and printed message | medium
modules.add: skip_install says to run hub install to pick up the new modules' dependencies | printed message | medium
modules.link: a checkout without .git is linked with a warning | printed message | medium
hub_install.read_hub_install: an alias in .zshrc is reported with its file | alias object | medium
identity SushiAccount.access_token: a token at exactly the 30 s refresh margin is refreshed | returned token under injected clock | small
pins.move_pin: a fragment already at the target version and commit is neither rewritten nor listed | file contents and return value | medium
releases.install_release: a refused resolve raises SushiAccountError and leaves nothing beside root | raised exception and directory listing | medium
update_check.latest_release: an unknown product gives no version and the reason | reason text | medium
tool_paths.rewrite_tool_paths: a drive letter in another case still moves on Windows | returned count | small
gui bridge Process: a child's non-zero exit code is returned by exit_code() | exit code of a spawned child | medium
```
