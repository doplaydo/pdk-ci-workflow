"""Tests for check_no_raw_layers hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from hooks.check_no_raw_layers import main


class TestCheckNoRawLayers:
    def test_clean_cells_pass(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_raw_tuple_in_layer_kwarg_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def bad_cell() -> gf.Component:
                    \"\"\"Bad cell.\"\"\"
                    c = gf.Component()
                    c.add_polygon([(0, 0), (1, 0), (1, 1)], layer=(1, 0))
                    return c
            """)
        )
        assert main() == 1

    def test_raw_tuple_in_non_layer_kwarg_passes(
        self, pdk_root: Path
    ) -> None:
        """Tuples in non-layer kwargs (center, size) should not be flagged."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def ok_cell() -> gf.Component:
                    \"\"\"OK cell.\"\"\"
                    c = gf.Component()
                    ref = c.add_ref(gf.components.rectangle(size=(10, 20)))
                    ref.move(center=(0, 0))
                    return c
            """)
        )
        assert main() == 0

    def test_raw_tuple_in_function_default_allowed(
        self, pdk_root: Path
    ) -> None:
        """Layer tuples in function defaults are allowed (LayerSpec defaults)."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def ok_cell(layer: tuple = (1, 0)) -> gf.Component:
                    \"\"\"OK cell.

                    Args:
                        layer: the layer.
                    \"\"\"
                    c = gf.Component()
                    return c
            """)
        )
        assert main() == 0

    def test_tech_py_files_skipped(self, pdk_root: Path) -> None:
        """tech.py and layers.py are allowed to have raw tuples."""
        # tech.py already exists; add a raw tuple to it
        (pdk_root / "my_pdk" / "tech.py").write_text(
            textwrap.dedent("""\
                LAYER_WG = (1, 0)
                LAYER_SLAB = (2, 0)
            """)
        )
        assert main() == 0

    def test_layer_slab_kwarg_caught(self, pdk_root: Path) -> None:
        """layer_slab is in the extended layer kwarg list."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def slab_cell() -> gf.Component:
                    \"\"\"Slab cell.\"\"\"
                    c = gf.Component()
                    c.add_polygon([(0, 0)], layer_slab=(3, 0))
                    return c
            """)
        )
        assert main() == 1

    def test_bbox_layers_kwarg_caught(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def boxed_cell() -> gf.Component:
                    \"\"\"Boxed cell.\"\"\"
                    c = gf.Component()
                    c.something(bbox_layers=(1, 0))
                    return c
            """)
        )
        assert main() == 1

    def test_positional_tuple_not_flagged(self, pdk_root: Path) -> None:
        """Tuples in positional arguments are not flagged (too ambiguous)."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                @gf.cell
                def ok_cell() -> gf.Component:
                    \"\"\"OK cell.\"\"\"
                    c = gf.Component()
                    c.move((1, 2))
                    return c
            """)
        )
        assert main() == 0

    @given(
        a=st.integers(min_value=0, max_value=255),
        b=st.integers(min_value=0, max_value=255),
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_any_int_tuple_in_layer_kwarg_caught(
        self, pdk_root: Path, a: int, b: int
    ) -> None:
        """Any (int, int) tuple in a layer= kwarg should be caught."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent(f"""\
                import gdsfactory as gf

                @gf.cell
                def cell_fn() -> gf.Component:
                    \"\"\"Cell.\"\"\"
                    c = gf.Component()
                    c.add_polygon([], layer=({a}, {b}))
                    return c
            """)
        )
        assert main() == 1

    def test_no_package_dir_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main() == 0

    def test_class_body_tuple_not_flagged(self, pdk_root: Path) -> None:
        """(int, int) inside a class body should not be flagged."""
        (pdk_root / "my_pdk" / "cells" / "waveguides.py").write_text(
            textwrap.dedent("""\
                import gdsfactory as gf

                class LayerConfig:
                    WG = (1, 0)
                    SLAB = (2, 0)

                @gf.cell
                def ok_cell() -> gf.Component:
                    \"\"\"OK cell.\"\"\"
                    return gf.Component()
            """)
        )
        assert main() == 0
