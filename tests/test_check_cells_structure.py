"""Tests for check_cells_structure hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hooks.check_cells_structure import main


class TestCheckCellsStructure:
    def test_valid_cells_pass(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_missing_cells_module_fails(self, pdk_root: Path) -> None:
        import shutil

        shutil.rmtree(pdk_root / "my_pdk" / "cells")
        assert main() == 1

    def test_cells_py_flat_layout_passes(self, pdk_root: Path) -> None:
        import shutil

        shutil.rmtree(pdk_root / "my_pdk" / "cells")
        (pdk_root / "my_pdk" / "cells.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def my_waveguide(width: float = 0.5) -> gf.Component:
                    \"\"\"A test waveguide.

                    Args:
                        width: waveguide width.
                    \"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 0

    def test_missing_docstring_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def no_docstring(width: float = 0.5) -> gf.Component:
                    return gf.Component()
            """)
        )
        assert main() == 1

    def test_missing_args_section_fails(self, pdk_root: Path) -> None:
        """Cell with parameters must have Args: section."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def missing_args(width: float = 0.5) -> gf.Component:
                    \"\"\"A component without Args section.\"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 1

    def test_no_args_section_ok_without_params(self, pdk_root: Path) -> None:
        """Cell without parameters doesn't need Args: section."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def no_params() -> gf.Component:
                    \"\"\"A component with no parameters.\"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 0

    def test_returns_component_without_decorator_fails(
        self, pdk_root: Path
    ) -> None:
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                def bare_component() -> gf.Component:
                    \"\"\"Returns a component without @gf.cell.\"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 1

    def test_private_function_skipped(self, pdk_root: Path) -> None:
        """Private functions (starting with _) should be skipped."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                def _helper() -> gf.Component:
                    return gf.Component()

                @gf.cell
                def public_cell() -> gf.Component:
                    \"\"\"A public cell.\"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 0

    def test_missing_init_reexport_fails(self, pdk_root: Path) -> None:
        """Cells not re-exported in __init__.py should fail."""
        # Add a new cell module not re-exported in init
        (pdk_root / "my_pdk" / "cells" / "couplers.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def coupler() -> gf.Component:
                    \"\"\"A coupler.\"\"\"
                    return gf.Component()
            """)
        )
        # __init__.py only imports waveguides, not couplers
        assert main() == 1

    def test_syntax_error_in_cell_warns(self, pdk_root: Path) -> None:
        """Syntax errors in cell files should warn but not crash."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            "def (:\n"
        )
        # Should not crash, and the syntax error cell is just warned about
        result = main()
        # result could be 0 (just warnings) since syntax errors produce warnings
        assert result in (0, 1)

    def test_cell_with_call_decorator_passes(self, pdk_root: Path) -> None:
        """@gf.cell() (with call) should be recognized."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell()
                def my_waveguide() -> gf.Component:
                    \"\"\"A test waveguide.\"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 0

    def test_no_package_dir_warns(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        # Should not crash, just warn
        assert main() == 0
