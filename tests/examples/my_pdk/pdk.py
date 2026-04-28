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
