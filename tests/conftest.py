"""Shared fixtures for pre-commit hook tests.

Every hook operates on the *current working directory*, so the central pattern
is:

1. ``tmp_path`` gives us an isolated directory.
2. ``monkeypatch.chdir(tmp_path)`` moves the CWD there.
3. Helper fixtures scaffold a minimal valid PDK repository layout so that
   individual tests only need to tweak the part they are testing.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest
import yaml


# ── Minimal valid content strings ────────────────────────────────────


MINIMAL_PYPROJECT = textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=68.0"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "my-pdk"
    version = "0.1.0"
    description = "A test PDK"
    requires-python = ">=3.9"
    readme = "README.md"
    license = {file = "LICENSE"}
    keywords = ["python", "photonics"]
    authors = [{name = "Test Author"}]
    dependencies = ["gdsfactory>=7.0"]
    classifiers = ["Development Status :: 3 - Alpha"]

    [dependency-groups]
    dev = ["pytest", "pytest-cov", "pytest_regressions", "pre-commit"]
    docs = ["jupytext", "jupyter-book"]

    [tool.ruff]
    fix = true

    [tool.ruff.lint]
    select = ["B", "C", "D", "E", "F", "I", "T10", "UP", "W"]
    ignore = ["E501", "B008", "C901", "B905", "C408"]

    [tool.ruff.lint.pydocstyle]
    convention = "google"

    [tool.codespell]
    ignore-words-list = "te,ba,fpr,ro,nd,donot,schem"

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    addopts = "--tb=short"

    [tool.setuptools.package-data]
    "*" = ["*.csv", "*.yaml", "*.yml", "*.gds", "*.lyp", "*.oas", "*.lyt"]

    [tool.setuptools.packages.find]
    where = ["."]
    include = ["my_pdk"]

    [tool.tbump.version]
    current = "0.1.0"

    [[tool.tbump.file]]
    src = "pyproject.toml"

    [[tool.tbump.file]]
    src = "my_pdk/__init__.py"

    [[tool.tbump.file]]
    src = "README.md"

    [tool.tbump.git]
    message_template = "Bump to {new_version}"
    tag_template = "v{new_version}"

    [tool.mypy]
    strict = true

    [tool.towncrier]
    directory = ".changelog.d"
    filename = "CHANGELOG.md"
    template = ".changelog.d/changelog_template.jinja"
""")


MINIMAL_INIT_PY = textwrap.dedent('''\
    """My PDK package."""

    __version__ = "0.1.0"
    __all__ = ["cells", "tech"]
''')


MINIMAL_TECH_PY = textwrap.dedent("""\
    import gdsfactory as gf

    LAYER = gf.typings.Layer
    LAYER_STACK = gf.typings.LayerStack
    LAYER_VIEWS = gf.typings.LayerViews
    cross_sections = {}
    routing_strategies = {}
""")


MINIMAL_CELL_PY = textwrap.dedent("""\
    import gdsfactory as gf

    @gf.cell
    def my_waveguide(width: float = 0.5) -> gf.Component:
        \"\"\"A test waveguide.

        Args:
            width: waveguide width.
        \"\"\"
        c = gf.Component()
        return c
""")

MINIMAL_CELLS_INIT = textwrap.dedent("""\
    from .waveguides import *
""")


MINIMAL_MAKEFILE = textwrap.dedent("""\
    install:
    \tuv sync

    test:
    \tuv run pytest

    test-force:
    \tuv run pytest --force-regen

    docs:
    \tjupyter-book build docs

    build:
    \tuv build

    update-pre:
    \tpre-commit autoupdate

    dev:
    \tuv sync --group dev
""")


MINIMAL_PRECOMMIT_CONFIG: dict[str, Any] = {
    "repos": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v4.5.0",
            "hooks": [
                {"id": "end-of-file-fixer"},
                {"id": "trailing-whitespace"},
            ],
        },
        {
            "repo": "local",
            "hooks": [
                {"id": "ruff-format", "name": "ruff-format", "entry": "ruff format", "language": "system", "types": ["python"]},
                {"id": "ruff-lint", "name": "ruff-lint", "entry": "ruff check", "language": "system", "types": ["python"]},
            ],
        },
        {
            "repo": "https://github.com/mwouts/nbstripout",
            "rev": "0.6.0",
            "hooks": [{"id": "nbstripout"}],
        },
        {
            "repo": "https://github.com/codespell-project/codespell",
            "rev": "v2.3.0",
            "hooks": [{"id": "codespell"}],
        },
    ]
}


MINIMAL_TEST_CODE_WORKFLOW: dict[str, Any] = {
    "name": "Test code",
    "on": {"push": None},
    "jobs": {
        "pre-commit": {
            "runs-on": "ubuntu-latest",
            "steps": [
                {"uses": "actions/checkout@v4"},
                {"uses": "pre-commit/action@v3"},
            ],
        },
        "test_code": {
            "runs-on": "ubuntu-latest",
            "steps": [
                {"uses": "actions/checkout@v4"},
                {"run": "make test"},
            ],
        },
    },
}


MINIMAL_RELEASE_DRAFTER_WORKFLOW: dict[str, Any] = {
    "name": "Release Drafter",
    "on": {"push": {"branches": ["main"]}},
    "jobs": {
        "update_release_draft": {
            "runs-on": "ubuntu-latest",
            "steps": [{"uses": "release-drafter/release-drafter@v5"}],
        }
    },
}


MINIMAL_PKD_INIT_PY = textwrap.dedent('''\
    from gdsfactory import Pdk
    from my_pdk.cells import waveguides
    from gdsfactory.get_factories import get_cells

    _cells = get_cells([waveguides])
    PDK = Pdk(
        name="my_pdk",
        cells=_cells,
        layers={},
        cross_sections={},
        layer_views=None,
        layer_stack=None,
        routing_strategies={},
    )
''')


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def pdk_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Scaffold a minimal valid PDK repo and chdir into it.

    Returns the tmp_path (== new CWD) so tests can mutate the tree.
    """
    monkeypatch.chdir(tmp_path)

    # Root files
    (tmp_path / "README.md").write_text("# My PDK\npip install my-pdk==0.1.0\n")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    (tmp_path / "pyproject.toml").write_text(MINIMAL_PYPROJECT)
    (tmp_path / "Makefile").write_text(MINIMAL_MAKEFILE)

    # .pre-commit-config.yaml
    (tmp_path / ".pre-commit-config.yaml").write_text(
        yaml.dump(MINIMAL_PRECOMMIT_CONFIG, default_flow_style=False)
    )

    # Package structure
    pkg = tmp_path / "my_pdk"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(MINIMAL_INIT_PY)
    (pkg / "tech.py").write_text(MINIMAL_TECH_PY)
    (pkg / "pdk.py").write_text(MINIMAL_PKD_INIT_PY)

    # cells subpackage
    cells = pkg / "cells"
    cells.mkdir()
    (cells / "__init__.py").write_text(MINIMAL_CELLS_INIT)
    (cells / "waveguides.py").write_text(MINIMAL_CELL_PY)

    # Tests
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_pdk.py").write_text(
        'from my_pdk import tech\ndef test_import(): assert tech\ndef test_difftest(): pass  # difftest()\n'
    )
    (tests / "gds_ref").mkdir()

    # Workflows
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "test_code.yml").write_text(
        yaml.dump(MINIMAL_TEST_CODE_WORKFLOW, default_flow_style=False)
    )
    (wf_dir / "release-drafter.yml").write_text(
        yaml.dump(MINIMAL_RELEASE_DRAFTER_WORKFLOW, default_flow_style=False)
    )

    # .changelog.d
    changelog_d = tmp_path / ".changelog.d"
    changelog_d.mkdir()
    (changelog_d / "changelog_template.jinja").write_text("{# template #}\n")

    return tmp_path
