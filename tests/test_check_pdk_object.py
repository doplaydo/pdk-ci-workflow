"""Tests for check_pdk_object hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hooks.check_pdk_object import main


class TestCheckPdkObject:
    def test_valid_pdk_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_no_pdk_call_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "pdk.py").write_text(
            "# No Pdk() call here\nx = 1\n"
        )
        # Also clear __init__.py to ensure no other Pdk call
        (pdk_root / "my_pdk" / "__init__.py").write_text(
            '__version__ = "0.1.0"\n__all__ = ["cells"]\n'
        )
        assert main() == 1

    def test_missing_required_kwargs_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "pdk.py").write_text(
            textwrap.dedent("""\
                from gdsfactory import Pdk
                PDK = Pdk(name="my_pdk")
            """)
        )
        assert main() == 1

    def test_missing_name_kwarg_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "pdk.py").write_text(
            textwrap.dedent("""\
                from gdsfactory import Pdk
                PDK = Pdk(cells={}, layers={}, cross_sections={})
            """)
        )
        assert main() == 1

    def test_missing_recommended_kwargs_only_warns(
        self, pdk_root: Path
    ) -> None:
        """Missing layer_views/layer_stack/routing_strategies should warn,
        not error."""
        (pdk_root / "my_pdk" / "pdk.py").write_text(
            textwrap.dedent("""\
                from gdsfactory import Pdk
                from gdsfactory.get_factories import get_cells
                from my_pdk.cells import waveguides

                _cells = get_cells([waveguides])
                PDK = Pdk(
                    name="my_pdk",
                    cells=_cells,
                    layers={},
                    cross_sections={},
                )
            """)
        )
        assert main() == 0

    def test_cells_without_get_cells_warns(self, pdk_root: Path) -> None:
        """cells= not using get_cells() should produce a warning, not error."""
        (pdk_root / "my_pdk" / "pdk.py").write_text(
            textwrap.dedent("""\
                from gdsfactory import Pdk
                PDK = Pdk(
                    name="my_pdk",
                    cells={"waveguide": lambda: None},
                    layers={},
                    cross_sections={},
                    layer_views=None,
                    layer_stack=None,
                    routing_strategies={},
                )
            """)
        )
        assert main() == 0

    def test_get_cells_via_variable_passes(self, pdk_root: Path) -> None:
        """get_cells() result stored in a variable should satisfy the check."""
        # This is the pattern in the default fixture; just verify it passes
        assert main() == 0

    def test_pdk_in_init_detected(self, pdk_root: Path) -> None:
        """Pdk() call in __init__.py should be detected."""
        (pdk_root / "my_pdk" / "pdk.py").write_text("# empty\n")
        (pdk_root / "my_pdk" / "__init__.py").write_text(
            textwrap.dedent("""\
                from gdsfactory import Pdk
                from gdsfactory.get_factories import get_cells

                __version__ = "0.1.0"
                __all__ = ["cells"]

                _cells = get_cells([])
                PDK = Pdk(
                    name="my_pdk",
                    cells=_cells,
                    layers={},
                    cross_sections={},
                    layer_views=None,
                    layer_stack=None,
                    routing_strategies={},
                )
            """)
        )
        assert main() == 0

    def test_gf_pdk_attribute_style_detected(self, pdk_root: Path) -> None:
        """gf.Pdk() style should also be detected."""
        (pdk_root / "my_pdk" / "pdk.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf
                from gdsfactory.get_factories import get_cells

                _cells = get_cells([])
                PDK = gf.Pdk(
                    name="my_pdk",
                    cells=_cells,
                    layers={},
                    cross_sections={},
                    layer_views=None,
                    layer_stack=None,
                    routing_strategies={},
                )
            """)
        )
        assert main() == 0

    def test_no_package_dir_warns(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main() == 0
