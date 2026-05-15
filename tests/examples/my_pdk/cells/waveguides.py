import gdsfactory as gf

@gf.cell
def my_waveguide(width: float = 0.5) -> gf.Component:
    """A test waveguide.

    Args:
        width: waveguide width.
    """
    c = gf.Component()
    return c
