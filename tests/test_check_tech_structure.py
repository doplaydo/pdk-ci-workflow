"""Tests for check_tech_structure hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hooks.check_tech_structure import main


class TestCheckTechStructure:
    def test_valid_tech_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_missing_tech_py_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "tech.py").unlink()
        assert main() == 1

    def test_missing_layer_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                LAYER_STACK = gf.typings.LayerStack
                LAYER_VIEWS = gf.typings.LayerViews
                cross_sections = {}
            """)
        )
        assert main() == 1

    def test_missing_layer_stack_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                LAYER = gf.typings.Layer
                LAYER_VIEWS = gf.typings.LayerViews
                cross_sections = {}
            """)
        )
        assert main() == 1

    def test_missing_layer_views_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                LAYER = gf.typings.Layer
                LAYER_STACK = gf.typings.LayerStack
                cross_sections = {}
            """)
        )
        assert main() == 1

    def test_missing_cross_sections_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                LAYER = gf.typings.Layer
                LAYER_STACK = gf.typings.LayerStack
                LAYER_VIEWS = gf.typings.LayerViews
            """)
        )
        assert main() == 1

    def test_missing_routing_strategies_warns(self, pdk_root: Path) -> None:
        """routing_strategies is recommended, not required."""
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                LAYER = gf.typings.Layer
                LAYER_STACK = gf.typings.LayerStack
                LAYER_VIEWS = gf.typings.LayerViews
                cross_sections = {}
            """)
        )
        assert main() == 0

    def test_syntax_error_in_tech_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "tech.py").write_text("def (:\n")
        assert main() == 1

    def test_imported_names_count(self, pdk_root: Path) -> None:
        """Names imported (not just assigned) should satisfy requirements."""
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                from my_pdk.layers import LAYER
                from my_pdk.stacks import LAYER_STACK, LAYER_VIEWS
                cross_sections = {}
                routing_strategies = {}
            """)
        )
        assert main() == 0

    def test_layers_yaml_consistency_warns(self, pdk_root: Path) -> None:
        """Mismatch between layers.yaml and code should warn but not fail."""
        # Create a layers.yaml with layers not in the code
        (pdk_root / "my_pdk" / "layers.yaml").write_text(
            "WG: [1, 0]\nSLAB: [2, 0]\nEXTRA: [99, 0]\n"
        )
        # Create layers.py with LAYER class
        (pdk_root / "my_pdk" / "layers.py").write_text(
            textwrap.dedent("""\
                class LAYER:
                    WG = (1, 0)
                    SLAB = (2, 0)
            """)
        )
        # Should still pass (mismatches are warnings)
        assert main() == 0

    def test_no_package_dir_warns(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main() == 0
