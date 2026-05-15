"""Tests for check_no_main_in_cells hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hooks.check_no_main_in_cells import main


class TestCheckNoMainInCells:
    def test_clean_cells_pass(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_main_guard_in_cell_fails(self, pdk_root: Path) -> None:
        cell_file = pdk_root / "my_pdk" / "cells" / "waveguides.py"
        cell_file.write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def my_waveguide():
                    \"\"\"A waveguide.\"\"\"
                    return gf.Component()

                if __name__ == "__main__":
                    c = my_waveguide()
                    c.show()
            """)
        )
        assert main() == 1

    def test_reversed_main_guard_also_caught(self, pdk_root: Path) -> None:
        cell_file = pdk_root / "my_pdk" / "cells" / "waveguides.py"
        cell_file.write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def my_waveguide():
                    \"\"\"A waveguide.\"\"\"
                    return gf.Component()

                if "__main__" == __name__:
                    pass
            """)
        )
        assert main() == 1

    def test_no_cells_passes(self, pdk_root: Path) -> None:
        """If there are no cell files, hook should pass."""
        import shutil

        shutil.rmtree(pdk_root / "my_pdk" / "cells")
        (pdk_root / "my_pdk" / "cells.py").write_text(
            "# empty cells module\nx = 1\n"
        )
        assert main() == 0

    def test_syntax_error_cell_skipped(self, pdk_root: Path) -> None:
        """Cells with syntax errors should be skipped (not crash)."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            "def (:\n"
        )
        assert main() == 0

    def test_no_package_dir_passes(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        """If no package dir is found, hook exits 0."""
        monkeypatch.chdir(tmp_path)
        assert main() == 0
