# Managed Core Runtime acquisition

The optional package exposes `xrefkit-openai-runtime-core`. Installing or
importing it and displaying its help require no Core lookup. Invoke this
entry point when a caller needs a compatible Core Runtime.

```text
xrefkit-openai-runtime-core --lock PATH --local-python INTERPRETER
xrefkit-openai-runtime-core --lock PATH --offline --wheelhouse DIRECTORY -- workflow --help
xrefkit-openai-runtime-core --lock PATH --offline --refresh
```

Supply a reviewed, target-specific JSON lock as a trusted deployment input.
Set `schema` to `1`, and set `target` to the Python implementation, exact
Python version and `sysconfig.get_platform()` joined with hyphens (for example
`cpython-3.12.9-win-amd64`). The `packages` object maps normalized package names
to objects with a pinned `version` and a nonempty `sha256` list of approved
wheel hashes. Include `xrefkit` and its entire target-specific dependency
closure. Managed setup requires a Python installation with venv and ensurepip (pip 22.3 or newer).

An explicit local interpreter must pass the target, Core version and
interface checks. Managed resolution otherwise uses the cache, a supplied
local wheelhouse, or the PyPI index. A wheelhouse disables index access.
`--offline` allows resolution from verified local inputs only. These flags
govern acquisition. A Core command passed after `--` retains its own behavior
and exit status.

With no Core command, the CLI emits a JSON resolution record that includes
the selected interpreter, source, Core version, binding schema revision,
Python target and lock digest.
Managed records also include wheel digests and environment generation.
Retain this record when pinning the interpreter for a run.

The cache is per-user by default. Use a trusted local filesystem and keep
the cache, lock and wheelhouse under the caller's control. A changed lock
selects a different entry. Invalid environments are rebuilt from verified
wheels when available. `--refresh` creates a new environment generation.
Old and incomplete generations are retained so an already-resolved
interpreter stays usable. Remove them only after confirming that no run
uses the cache.

## Installed Windows commands

The wheel contains the approved Windows x64 / CPython 3.12.9 lock for
Core 0.7.13 and the SHA-256-pinned startup contract.

- Run `xrefkit-openai-runtime-core` to acquire the bundled Core lock from
  PyPI. Use `--offline --wheelhouse PATH` to seed the same cache locally.
- From a confirmed local Desktop turn, run
  `xrefkit-openai-runtime-desktop --journal PATH --turn-id TURN`. The
  host supplies the same verified origin snapshots as the repository CLI.
  The installed command uses the bundled contract and the offline cache.
  It supports the stub workflow and recovery of its results.
- The default per-user Core cache is
  `%LOCALAPPDATA%\xrefkit-openai-runtime\Cache`. Desktop admission state
  is stored at `%LOCALAPPDATA%\XRefKit\desktop-api-host.sqlite`.
