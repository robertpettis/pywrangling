import matplotlib.pyplot as plt

def set_top_ylabel(ax, label, pad=0.02, **text_kwargs):
    """
    Place a horizontal label ABOVE the axes (centered over the y-axis),
    instead of using the standard vertical y-axis label on the side.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to draw the label on.
    label : str
        The text of the label.
    pad : float, optional (default=0.02)
        Extra spacing above the axes in axes-relative units (0–1).
    text_kwargs :
        Extra keyword arguments forwarded to `ax.text()`, such as:
        - fontsize
        - fontweight
        - color
        - etc.

    Usage
    -----
    >>> fig, ax = plt.subplots()
    >>> ax.plot(x, y)  # your data
    >>> set_top_ylabel(ax, "Y", fontsize=12) ### Use this instead of ax.set_ylabel("Y")
    >>> ax.set_xlabel("X")
    >>> plt.show()

    This replaces the usual:
        ax.set_ylabel("Y")
    but keeps the label horizontal and centered at the top.
    """
    ax.text(
        0.0,                # x: exactly on the y-axis
        1.0 + pad,          # y: slightly above the top of the axes
        label,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        rotation=0,
        **text_kwargs,
    )
