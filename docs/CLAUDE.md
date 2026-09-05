# CLAUDE.md

## Getting oriented

When starting work on this project:

1. Read `docs/CONTRIBUTING.md` and `docs/DOCUMENTATION_STYLE_GUIDE.md` first and follow them.
2. Read `docs/README.md` and every page it links under the manual headings to build context before
   making changes. `docs/agent/` is a record of past work; read the design it names when your task
   touches that area.
3. `docs/design/REMAINING_WORK.md` is the single backlog. A task that adds or finishes work updates
   it in the same commit.

## How to work

Act as an expert in whatever role the task requires, and work with real engineering discipline,
not a quick hack that happens to pass.

### Priority 1: Maintainability

Everything must be SOLID and heavily encapsulated within its own boundaries. Every module should be
so well-isolated that changes stay local instead of rippling across the codebase, and anything can
be found quickly by someone looking for it. This is the single biggest determinant of the project's
long-term fate, which is why it comes before everything else, including performance.

### Priority 2: Performance

Treat wasted cycles as a real cost. The guiding principle is "engineer it once carefully, run it a
thousand times cheaply": invest the effort up front so the result is efficient every time it runs.

### Quality bar

Hold an extremely high standard of quality and correctness. "Good enough for now" is not acceptable.

### Honesty

Always be honest. If a task turns out to be too large to finish, never quietly cut corners and claim
it is done. Say plainly what was completed and what was not. If a task requires a choice, ask rather
than picking arbitrarily.

### Building

Never invoke the underlying build system (ninja, cmake, ctest) directly, and never run a real build
to prove a CLI change. `tools/record_cli_argv.py` captures what a CLI would send to cmake without
compiling; that is the evidence.

### Task tracking

For every implementation, create tasks up front and update the list as work progresses.
