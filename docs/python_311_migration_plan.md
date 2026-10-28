# Python 3.11 minimum support and typing — Semblance 0.10.0

Status: implemented in source. The Python 3.11 environment, package metadata,
typing changes, documentation, changelogs, CI matrices, and release tags are
prepared. CI still needs to pass before publishing any package.

## Release scope

Semblance **0.10.0** will require **Python >=3.11** and use typing features
available in Python 3.11 throughout the maintained workspace. Dropping Python
3.10 is an intentional compatibility break and must appear prominently in the
release notes. Existing application behavior, HTTP contracts, and fixture formats
should remain compatible on supported interpreters.

Apply the same baseline to new Foundry and Databricks adapter releases. They
remain independently versioned; the proposed coordinated releases are:

| Package | Last published version | Prepared source version | Release tag |
|---|---|---|---|
| `semblance` | 0.9.2 | **0.10.0** | `v0.10.0` |
| `semblance-foundry` | 0.1.3 | **0.2.0** | `foundry-v0.2.0` |
| `semblance-databricks` | 0.1.2 | **0.2.0** | `databricks-v0.2.0` |

The adapter minor bumps communicate the interpreter support break. Set their
core dependency to `semblance>=0.10.0,<1.0` so this release set has one baseline.
Previously published adapter versions keep their existing metadata.

## Starting baseline

- All three `pyproject.toml` files require `>=3.10` and advertise 3.10–3.12.
- Root Ruff targets `py310`; mypy targets `3.10`. Ruff already enables `UP`
  rules, and all three source packages require annotated function definitions.
- CI and release workflows test three packages on Python 3.10, 3.11, and 3.12
  across Linux, macOS, and Windows. Type checking currently runs on 3.12.
- Most code already uses `list[T]`, `dict[K, V]`, `T | None`, and
  `collections.abc` imports. This is a targeted migration, not a wholesale rewrite.
- `src/semblance/config.py` falls back from `tomllib` to `tomli` and contains
  compatibility-related casts and ignores.
- Both adapters have `py.typed`; core currently has no marker. Local mypy source
  checks alone do not validate the experience of an installed package consumer.
- The repository `.venv` has been replaced with a Python 3.11 environment and
  installed with all package development and documentation extras.

## Typing standard for this release

Use the following conventions in source, maintained tests, examples, and Python
snippets. Python 3.11 is the syntax ceiling even when checks run on newer Python.

| Area | Convention |
|---|---|
| Collections and unions | Continue using `list[T]`, `dict[K, V]`, `tuple[...]`, `type[T]`, and `T | None`; use `collections.abc` for abstract interfaces such as `Mapping`, `Sequence`, and `Callable`. |
| Constructors and fluent methods | Use `typing.Self` for methods that preserve the receiving subclass, starting with `SemblanceAPI.from_config()` and both adapters' `load_fixture()` / `load_bundled_fixture()`. See [PEP 673](https://peps.python.org/pep-0673/). |
| Fixed dictionary shapes | Use `TypedDict` with `Required` / `NotRequired` where a stable internal shape warrants it; missing keys and nullable values are distinct. Audit config dictionaries first, while preserving existing config defaults and parsing behavior. See [PEP 655](https://peps.python.org/pep-0655/). |
| Generics and aliases | Keep `TypeVar` plus `Generic[T]` for `PaginatedResponse` and `PageSlice`; use `TypeAlias` for explicit aliases where useful. |
| Dynamic boundaries | Keep justified `Any` for dynamic Pydantic models, arbitrary request data, and plugin values; prefer specific types or `object` where callers must narrow a value. Avoid blanket casts or new global mypy exemptions. |
| Type assertions | Use `typing.assert_type` in dedicated static checks; use `assert_never` only for branches that are actually exhaustive. |
| Runtime annotations | Preserve `Annotated` metadata and `get_type_hints(..., include_extras=True)` in link resolution. Keep runtime-required imports available; review any move behind `TYPE_CHECKING`. |
| Backports | Import features available in 3.11 from `typing`. No direct `typing_extensions` import currently needs migration; do not remove a transitive dependency required by another library. |

These conventions use the [Python 3.11 typing APIs](https://docs.python.org/3.11/library/typing.html).
Do not introduce `class Model[T]`, `def helper[T]`, or `type Alias = ...`:
[PEP 695](https://peps.python.org/pep-0695/) requires Python 3.12.
Likewise, standard-library `typing.override` is outside the 3.11 baseline.
`LiteralString`, variadic generics, and `dataclass_transform` are available in
3.11 but should be adopted only for an actual API need, not to demonstrate every
new typing feature. Retain existing postponed annotations where useful; removing
them is not required by this migration.

## Implementation sequence

### 1. Align interpreter metadata and tooling

- [x] Recreate the development environment with Python 3.11 and install all
  three packages with their development extras; verify documentation tools too.
- [x] Change `requires-python` to `>=3.11` in the root and both adapter
  `pyproject.toml` files; remove their Python 3.10 classifiers.
- [x] Set root Ruff `target-version = "py311"` and mypy
  `python_version = "3.11"`. Keep the shared source paths and annotated-definition
  requirements for all three packages.
- [x] Preserve the existing Ruff pin across the root dev extra and pre-commit /
  workflow installations. Run the existing `UP` rules with the new target and
  review fixes, especially annotation changes used by FastAPI or Pydantic.
- [x] Do not enable blanket mypy strictness or unsafe fixes as part of the
  interpreter bump. Remove obsolete ignores as their causes are resolved.

### 2. Remove compatibility code and improve applicable annotations

- [x] Replace the `tomli` fallback in `src/semblance/config.py` with direct
  standard-library `tomllib` loading, available since
  [Python 3.11](https://docs.python.org/3.11/whatsnew/3.11.html#tomllib).
  Either inline `_toml_load` or give the retained helper an appropriate binary
  file interface; remove compatibility casts and ignores that become unnecessary.
- [x] Preserve config discovery, missing-file defaults, malformed-input behavior,
  YAML handling, and keyword overrides. Add focused coverage for any gaps exposed
  by removing the fallback, including successful TOML loading without `tomli`.
- [x] Apply `Self` to the concrete constructor and fluent-method candidates above.
  Check subclass return inference and runtime subclass preservation.
- [x] Audit bare collections, redundant quoted annotations, fixed dictionary
  shapes, and callback signatures in changed code. Make targeted improvements
  without redesigning the plugin registry or vendor response models.
- [x] Review maintained examples and snippets, including the CLI scaffold in
  `src/semblance/cli.py`; Ruff currently excludes `docs/` and `examples/`, so they
  require an explicit audit. Keep generic pagination definitions valid on 3.11.

### 3. Make published typing usable

- [x] Add `src/semblance/py.typed` and explicitly include it in root setuptools
  package data; retain both adapters' existing markers. This follows the
  [typing distribution specification](https://typing.python.org/en/latest/spec/distributing.html#packaging-type-information).
- [x] Build wheels in CI and inspect their contents
  and `Requires-Python` metadata. Ensure source distributions retain the markers
  so rebuilding wheels preserves them.
- [x] Add a small consumer typing check outside the source tree, using installed
  wheels without `MYPYPATH` or repository source-path overrides. Exercise public
  imports, `Self` subclass inference, typed pagination items, and a custom
  `LinkProtocol` implementation. Run it in CI explicitly; normal pytest execution
  does not enforce `assert_type` assertions.

### 4. Align CI and release gates

- [x] Update **both** `.github/workflows/ci.yml` and
  `.github/workflows/release.yml`: remove Python 3.10 from test matrices and keep
  3.11 and 3.12 across all existing OS and package slices.
- [x] Run mypy on Python 3.11 in both workflows, with the configured 3.11 target.
  Other tooling jobs can stay on 3.12; the Read the Docs 3.12 builder is compatible
  with the new minimum and does not require changing.
- [x] Add the installed-wheel consumer typing check before publishing. Run
  wheel-install and CLI/import smoke checks on Python 3.11.
- [x] Set wheel `Requires-Python` metadata to `>=3.11`; the release matrix no
  longer provisions Python 3.10.
- [x] Retain lint, formatting, documentation, security, and separate package test
  gates. Keep SDK checks optional as today.

The required matrix for this migration is 3.11–3.12. Adding newer interpreters is
separate compatibility work: validate dependencies and all package slices before
adding corresponding classifiers or making a tested-support claim.

### 5. Document and prepare the release

- [x] Update Python requirements in `README.md`, `docs/index.md`,
  `docs/guides/getting-started.md`, both adapter READMEs, and `CONTRIBUTING.md`.
- [x] Add the typing conventions to the contributor guide. Remove the Python
  3.10 / `tomli` installation guidance from `docs/guides/cli.md`.
- [x] Update adapter compatibility guidance in `docs/guides/foundry.md` and
  `docs/guides/databricks.md`, and annotate old adapter-plan Python matrices as
  historical or superseded by this plan.
- [x] Update all three changelogs and `docs/publishing.md` with the coordinated
  versions and tags. Update adapter `_distribution_version()` fallbacks in their
  `app.py` files when bumping versions.
- [x] State prominently: upgrade to Python 3.11+ before installing 0.10.0;
  Python 3.10 users must remain on `semblance<0.10` and the previously published
  adapter releases (`<0.2`). An unpinned install may select an older compatible
  release rather than fail.
- [x] Add 0.10.x to `SECURITY.md` without implying new support
  commitments or changing the maintenance policy for older releases.
- [x] Prepare dated release notes, source version bumps, compare links, and
  publishing instructions for core `v0.10.0` and adapter `v0.2.0` releases.
  Publishing remains a later release action.

## Acceptance criteria

- [ ] All three distributions declare Python >=3.11 and ship usable typing
  markers; built artifacts reject explicit installation on 3.10.
- [ ] Ruff and mypy target 3.11; source and generated examples contain no syntax
  requiring 3.12+. Installed consumers get the intended public types.
- [ ] Core, Foundry, and Databricks tests pass on 3.11 and 3.12 across Linux,
  macOS, and Windows in CI and release workflows.
- [ ] Config behavior, `Annotated` link resolution, generic pagination, subclass
  return types, CLI scaffolding, and public import boundaries are verified.
- [ ] Ruff, formatting, mypy, security checks, `mkdocs build --strict`, and
  `tests/test_doc_examples.py` pass. No new broad type-checker exemptions.
- [ ] Versions, dependency bounds, changelogs, support guidance, and release tags
  agree; the documented compatibility break is limited to interpreter support
  and intentional annotation improvements.
