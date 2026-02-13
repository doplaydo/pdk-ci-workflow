# hooks/

Pre-commit hook scripts for PDK template compliance. These are referenced by `.pre-commit-hooks.yml` at the repository root and executed by the [pre-commit](https://pre-commit.com/) framework when consuming repos point to this repository in their `.pre-commit-config.yaml`.

Each hook is a self-contained Python script that validates some aspect of a PDK repository's structure and configuration. Hooks use **errors** for required items (fail the hook) and **warnings** for recommended items (print but pass).

## Available Hooks (15)

### Project Structure

| Hook ID | Source | What it checks |
|---------|--------|---------------|
| `check-required-files` | `check_required_files.py` | README.md, CHANGELOG.md, LICENSE, Makefile, pyproject.toml, .gitignore, .pre-commit-config.yaml, tests/ directory, test workflow, release-drafter workflow |
| `check-pyproject-sections` | `check_pyproject_sections.py` | 11 sub-checks: build-system, project fields, optional deps (dev/docs), ruff config, ruff per-file-ignores, codespell, pytest, package-data, tbump, mypy, towncrier |
| `check-package-init` | `check_package_init.py` | Top-level `__init__.py` defines `__version__` as string literal and `__all__` for public API |
| `check-version-sync` | `check_version_sync.py` | Version consistency across pyproject.toml `[project].version`, `[tool.tbump.version].current`, `__init__.py __version__`, and README.md pip install line |

### Cells & Technology

| Hook ID | Source | What it checks |
|---------|--------|---------------|
| `check-cells-structure` | `check_cells_structure.py` | `@gf.cell` decorators on component functions, Google-style docstrings with `Args:` section, `cells/__init__.py` re-exports all cell modules |
| `check-tech-structure` | `check_tech_structure.py` | `tech.py` defines LAYER, LAYER_STACK, LAYER_VIEWS, cross_sections (required) and routing_strategies (recommended); cross-checks with layers.yaml if present |
| `check-pdk-object` | `check_pdk_object.py` | `Pdk()` constructor called with required kwargs (name, cells, layers, cross_sections), recommended kwargs (layer_views, layer_stack, routing_strategies), and `cells=` uses `get_cells()` |
| `check-no-raw-layers` | `check_no_raw_layers.py` | Flags `(int, int)` tuples in cell files that should use `LAYER.XXX` constants; skips tech.py, layers.py, function defaults, and class attributes |
| `check-no-main-in-cells` | `check_no_main_in_cells.py` | Flags `if __name__ == "__main__"` blocks in cell files |

### Infrastructure

| Hook ID | Source | What it checks |
|---------|--------|---------------|
| `check-test-structure` | `check_test_structure.py` | `tests/` directory exists with test files, GDS reference directories, `difftest()` calls, and `data_regression` usage |
| `check-makefile-targets` | `check_makefile_targets.py` | Required targets: install, test. Recommended: docs, build, test-force, update-pre. Content checks: uv sync in install, pytest in test |
| `check-workflows` | `check_workflows.py` | `.github/workflows/` has test_code.yml (or test.yml) with pre-commit job and test job; recommends release.yml |
| `check-precommit-config` | `check_precommit_config.py` | `.pre-commit-config.yaml` includes required hooks (end-of-file-fixer, trailing-whitespace, ruff, ruff-format) and recommended hooks (nbstripout, codespell) |

### Multi-band & Dependencies

| Hook ID | Source | What it checks |
|---------|--------|---------------|
| `check-multi-band` | `check_multi_band.py` | For multi-band PDKs (2+ band directories): consistent module sets per band (cells, tech, models), corresponding test files, shared layers at package root. Silently passes for single-band PDKs. |
| `requires-pytz` | `check_requires_pytz.py` | Ensures `pytz` is in `[project.dependencies]` of pyproject.toml; auto-injects if missing |

## Shared Utilities (`_utils.py`)

All hooks share common infrastructure from `_utils.py`:

- **`CheckResult`** - Accumulates errors and warnings, prints a summary, and returns 0 (pass) or 1 (fail)
- **`load_toml()`** / **`load_yaml()`** - Parse pyproject.toml and YAML files with error handling
- **`find_package_dir()`** - Discovers the PDK package directory from pyproject.toml configuration or directory scanning
- **`find_band_dirs()`** - Locates band subdirectories in multi-band PDKs (subdirs with `__init__.py` + `cells/` or `tech.py`)
- **`find_cell_files()`** - Discovers all Python cell files in `cells/` directories
- **`get_pdk_subdirs()`** - Returns band directories for multi-band PDKs, or `[pkg_dir]` for flat PDKs
- **AST helpers** - `parse_file()`, `find_assignments()`, `get_assigned_string()`, `has_if_name_main()`, `get_import_aliases()`, `is_gf_cell_decorator()`, `returns_component()`, `has_google_args_section()`

## Hook Design Pattern

Every hook follows the same structure:

```python
"""Pre-commit hook: <description>."""
from __future__ import annotations
import sys
from hooks._utils import CheckResult

def main() -> int:
    result = CheckResult("hook-name")
    # ... validation logic ...
    result.error("Something required is missing")    # Hard failure
    result.warn("Something recommended is missing")  # Printed but passes
    return result.report()

if __name__ == "__main__":
    sys.exit(main())
```

- Entry points are registered in `pyproject.toml` under `[project.scripts]`
- Hook metadata is registered in `.pre-commit-hooks.yml`
- All hooks use `always_run: true` and `pass_filenames: false` (repo-level structural checks)

## Adding a New Hook

1. Create `hooks/check_<name>.py` following the pattern above
2. Add an entry point to `pyproject.toml`:
   ```toml
   check_<name> = "hooks.check_<name>:main"
   ```
3. Register in `.pre-commit-hooks.yml`:
   ```yaml
   - id: check-<name>
     name: <Human-readable name>
     entry: check_<name>
     language: python
     always_run: true
     pass_filenames: false
     description: >
       <What it checks>
   ```
4. Add the hook ID to `templates/.pre-commit-config.yaml`
5. Test locally:
   ```bash
   pre-commit try-repo . check-<name> --verbose --all-files
   ```
