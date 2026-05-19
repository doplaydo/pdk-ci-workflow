"""Build a cell and write it to build/gds/<cell_name>.gds.

When cell_name is "all_cells", builds every PDK-owned cell that can be
instantiated with default arguments and packs them into a single GDS.
Cells from installed packages (site-packages / .venv), cells located
under a ``samples/`` directory (demo/tapeout cells that reuse BB cells
and would cause cellname collisions), and cells that require positional
arguments are skipped automatically.
"""

import importlib
import inspect
import sys
from pathlib import Path

from gdsfactoryplus.core.pdk import get_pdk, register_cells

cell_name = sys.argv[1]
Path("build/gds").mkdir(parents=True, exist_ok=True)
register_cells()
pdk = get_pdk()

if cell_name == "all_cells":
    import gdsfactory as gf

    c = gf.Component("all_cells")
    for name, func in sorted(pdk.cells.items()):
        # Skip cells from installed packages (not PDK-owned)
        try:
            src = inspect.getfile(inspect.unwrap(func))
        except TypeError:
            continue
        if ".venv" in src or "site-packages" in src:
            continue

        # Skip demo/tapeout cells under a samples/ directory: they reuse BB
        # cells already registered as top-level PDK cells, which would cause
        # cellname collisions when packed together.
        if "/samples/" in src or src.endswith("/samples"):
            print(f"Skipping {name}: in samples/")
            continue

        # Skip cells that require positional arguments
        sig = inspect.signature(func)
        required = [
            p
            for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
            and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]
        if required:
            print(f"Skipping {name}: requires arguments {[p.name for p in required]}")
            continue

        try:
            c.add_ref(func())
        except Exception as e:  # noqa: BLE001
            print(f"Error instantiating cell {name}: {e}")
    c.write_gds(f"build/gds/{cell_name}.gds")
else:
    candidate_names = [cell_name, f"_{cell_name}"]
    cell_func = None

    for candidate_name in candidate_names:
        cell_func = pdk.cells.get(candidate_name)
        if cell_func:
            break

    if cell_func is None:
        # Cell not auto-discovered (e.g. nested in a samples/ subpackage).
        for py_file in sorted(Path(".").rglob(f"{cell_name}.py")):
            module_path = ".".join(py_file.with_suffix("").parts)
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                continue
            for candidate_name in candidate_names:
                cell_func = getattr(mod, candidate_name, None)
                if cell_func:
                    break
            if cell_func:
                break

    if cell_func is None:
        print(f"Error: cell '{cell_name}' not found", file=sys.stderr)
        sys.exit(1)

    c = cell_func()
    c.write_gds(f"build/gds/{cell_name}.gds")
