import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patheffects as pe


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


def pick_label_xy(x, y, ax, prefer="whitespace", n_candidates=25):
    """
    Pick a "good" (x, y) point along a line to place a label.

    The idea:
    - We only consider existing data points (so labels sit *on* the line).
    - If `prefer="whitespace"`, we score each candidate by how "empty" the
      surrounding neighborhood is (in screen/pixel space), and pick the best.

    Parameters
    ----------
    x, y : array-like
        1D sequences of x and y values (same length).
    ax : matplotlib.axes.Axes
        Axes the line is being plotted on (used for coordinate transforms).
    prefer : {"whitespace", "middle"}, default "whitespace"
        Strategy for picking a label location:
        - "whitespace": choose a point with the most nearby empty space.
        - "middle": choose a point near the middle of the series.
    n_candidates : int, default 25
        How many candidate points to evaluate (subsampled across the series).

    Returns
    -------
    (x0, y0) : tuple[float, float]
        The chosen label location in *data coordinates*.
    """
    # Convert to numpy arrays and drop NaNs so transforms/scoring don't break.
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]

    # If nothing usable, return NaNs (caller can handle).
    if len(x) == 0:
        return (np.nan, np.nan)

    # "Middle" is a simple fallback strategy (no scoring).
    if prefer == "middle":
        i = len(x) // 2
        return (float(x[i]), float(y[i]))

    # --- Whitespace-based selection ---
    #
    # We score each candidate point by its distance to the nearest other point
    # in *display coordinates* (pixels). Bigger distance => more empty space.
    #
    # This is a crude proxy for "will a text label likely collide with stuff?"
    # but it tends to work well and is fast for typical line lengths.

    # Choose evenly-spaced candidate indices (avoid endpoints a bit if possible).
    if len(x) <= n_candidates:
        cand_idx = np.arange(len(x))
    else:
        cand_idx = np.linspace(0, len(x) - 1, n_candidates).round().astype(int)

    # Transform all points from data coordinates -> display/pixel coordinates.
    # This makes spacing comparable even when axes are log-scaled or stretched.
    pts_disp = ax.transData.transform(np.column_stack([x, y]))

    # Score each candidate by its nearest-neighbor distance.
    best_i = int(cand_idx[len(cand_idx) // 2])  # sensible fallback
    best_score = -np.inf

    for i in cand_idx:
        # Distances from candidate i to every other point, in pixels.
        d = np.sqrt(((pts_disp - pts_disp[i]) ** 2).sum(axis=1))

        # Ignore distance to itself (0) by taking the *second* smallest distance
        # if possible. If only one point, whitespace is "infinite".
        if len(d) <= 1:
            score = np.inf
        else:
            score = np.partition(d, 1)[1]

        if score > best_score:
            best_score = score
            best_i = int(i)

    return (float(x[best_i]), float(y[best_i]))


def label_line(
    ax,
    x,
    y,
    text,
    *,
    manual_xy=None,
    prefer="whitespace",
    dx=8,
    dy=8,
    print_xy=True,
    fontsize=11,
    fontfamily=None,
    fontweight=None,
    fontstyle=None,
    add_outline=True,
    text_kwargs=None,
    **plot_kwargs,
):
    """
    Plot a line and place a label *on the line* with the label color matching the line.

    This function is designed to be a nice replacement for the common pattern:
        ax.plot(x, y)
        ax.text(...)

    It:
    1) plots the line (returns the Line2D),
    2) chooses a good label position automatically (or uses manual_xy),
    3) annotates text with the same color as the line,
    4) optionally prints the chosen (x, y) so you can manually tweak later,
    5) optionally adds a white outline behind the text to keep it readable.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to draw on.
    x, y : array-like
        1D sequences of x and y values. NaNs are allowed; they are ignored for labeling.
    text : str
        The text label to draw on the line.

    manual_xy : tuple[float, float] or None, default None
        If provided, the label is placed at (x0, y0) in *data coordinates*.
        This overrides the automatic placement algorithm.

    prefer : {"whitespace", "middle"}, default "whitespace"
        Automatic placement strategy (only used if manual_xy is None).
        - "whitespace": choose a point that has the most nearby empty space.
        - "middle": choose a point near the middle of the series.

    dx, dy : float, default 8, 8
        Offset for the label in *points* (screen units). The label is anchored
        at the chosen point (x0, y0), and then shifted by (dx, dy) for legibility.

    print_xy : bool, default True
        If True, print the chosen (x, y) label position (data coords). This makes
        it easy to rerun with a manual override:
            label_line(..., manual_xy=(x0, y0), print_xy=False)

    fontsize : int or float, default 11
        Font size for the label.

    fontfamily : str or None, default None
        Font family name (e.g., "DejaVu Sans", "Arial").

    fontweight : str or None, default None
        Font weight (e.g., "normal", "bold").

    fontstyle : str or None, default None
        Font style (e.g., "normal", "italic").

    add_outline : bool, default True
        If True, add a white outline behind the text to improve readability
        on top of the line.

    text_kwargs : dict or None, default None
        Extra keyword args forwarded to `ax.annotate(...)` (e.g., alpha, rotation).

    **plot_kwargs
        Any other keyword args forwarded to `ax.plot(...)` (e.g., marker, linewidth).

    Returns
    -------
    line : matplotlib.lines.Line2D
        The plotted line object.
    xy : tuple[float, float]
        The label anchor point used (x0, y0) in data coordinates.

    Example
    -------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>>
    >>> x = np.arange(1, 15)
    >>> y1 = np.log(x) + 0.1*np.sin(x)
    >>> y2 = np.log(x) - 0.2 + 0.1*np.cos(x)
    >>>
    >>> fig, ax = plt.subplots(figsize=(8, 4))
    >>> label_line(ax, x, y1, "Series A", marker="o", fontsize=12, fontweight="bold")
    >>> label_line(ax, x, y2, "Series B", marker="o", fontsize=12, fontstyle="italic")
    >>> ax.set_title("Line labels that match line colors")
    >>> plt.tight_layout()
    >>> plt.show()
    >>>
    >>> # If you want to manually place after seeing output:
    >>> # label_line(ax, x, y1, "Series A", manual_xy=(10, y1[9]), print_xy=False)
    """
    # Default to an empty dict so we can safely unpack it later.
    if text_kwargs is None:
        text_kwargs = {}

    # --- 1) Plot the line and capture the returned Line2D object ---
    #
    # Using (line,) = ax.plot(...) ensures we get exactly the line object.
    (line,) = ax.plot(x, y, **plot_kwargs)

    # Ensure the axes limits are updated so coordinate transforms and placement
    # behave correctly even if the user hasn't called autoscale yet.
    ax.relim()
    ax.autoscale_view()

    # --- 2) Choose the anchor point (x0, y0) where the label will attach ---
    #
    # If manual_xy is provided, use it directly. Otherwise choose automatically.
    if manual_xy is not None:
        x0, y0 = manual_xy
    else:
        x0, y0 = pick_label_xy(x, y, ax, prefer=prefer)

    # --- 3) Match label color to the plotted line color ---
    #
    # This is what you asked for: no box, same color as the line.
    line_color = line.get_color()

    # --- 4) Add the text label ---
    #
    # We use annotate() instead of text() because annotate supports offset
    # via "offset points" in a clean way while still anchoring to (x0, y0).
    ann = ax.annotate(
        text,
        xy=(x0, y0),              # anchor point in data coordinates
        xytext=(dx, dy),          # shift label in points
        textcoords="offset points",
        ha="left",
        va="bottom",
        color=line_color,
        fontsize=fontsize,
        fontfamily=fontfamily,
        fontweight=fontweight,
        fontstyle=fontstyle,
        **text_kwargs,
    )

    # --- 5) Optional readability outline (no box) ---
    #
    # This outlines the text with a white stroke so it remains readable even if
    # the line passes behind the letters.
    if add_outline:
        ann.set_path_effects([
            pe.Stroke(linewidth=3, foreground="white"),
            pe.Normal(),
        ])

    # --- 6) Optional: print chosen coordinates so you can override manually ---
    if print_xy:
        print(f"[label_line] '{text}' at data coords: (x={x0:.4f}, y={y0:.4f})")

    return line, (x0, y0)












def use_plotplainblind_matched(kind="line"):
def use_plotplainblind_matched(kind="line"):
    """
    Configure Matplotlib rcParams to mimic Stata's `plotplainblind` scheme
    (color/linestyle/marker ordering) and a "plain" white-background aesthetic.

    This is meant to be called once near the top of a plotting script (or at the
    start of a notebook cell) before you create figures. It updates global
    Matplotlib settings via `matplotlib.rcParams.update(...)` and sets an
    `axes.prop_cycle` that controls the default sequence of colors/linestyles/
    markers applied as you add multiple series.

    Parameters
    ----------
    kind : {"line", "scatter", "connected", "mono"}, default "line"
        Controls how the Stata-like ordering is emulated:

        - "line":
            Cycle through a Stata-ish palette while also cycling linestyles.
            Use when you have multiple lines and want them differentiated even
            if printed in grayscale.
        - "scatter":
            Cycle through colors while also cycling markers.
            Use for point-only plots where shape matters.
        - "connected":
            Cycle through colors + linestyles + markers.
            Use for connected scatterplots / time series with markers.
        - "mono":
            Force a single grayscale color (useful for bars/box/dot/errorbars
            when you want everything uniform).

    Notes
    -----
    - This function mutates global Matplotlib defaults (rcParams). If you want
      the style to apply only within a specific block, wrap calls in
      `with plt.rc_context(): ...` and call this inside the context.
    - The label utilities in this module are designed to pair nicely with this
      style:
        * `label_line(...)` places a text label directly on the line in the same
          color as the line (optionally with a white stroke for readability).
        * `pick_label_xy(...)` chooses a good anchor point for the label.
        * `set_top_ylabel(...)` places a horizontal y-label above the axes.

    Full Example
    ------------
    This example uses *all* helpers above: style setup, top y-label, and
    color-matched on-line labels with automatic placement.

    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>>
    >>> # 1) Apply Stata-like style + cycle logic
    >>> use_plotplainblind_matched(kind="connected")
    >>>
    >>> # 2) Fake data: three series with different shapes
    >>> x = np.arange(1, 25)
    >>> y_a = np.log(x) + 0.08*np.sin(x)
    >>> y_b = np.log(x) - 0.25 + 0.06*np.cos(1.2*x)
    >>> y_c = np.log(x) - 0.50 + 0.04*np.sin(0.7*x + 1.0)
    >>>
    >>> # 3) Build figure
    >>> fig, ax = plt.subplots(figsize=(9, 4.5))
    >>>
    >>> # 4) Plot + label each line directly (no legend needed)
    >>> label_line(ax, x, y_a, "Series A", prefer="whitespace")
    >>> label_line(ax, x, y_b, "Series B", prefer="whitespace")
    >>> label_line(ax, x, y_c, "Series C", prefer="whitespace")
    >>>
    >>> # 5) Axis labeling (y label on top, Stata-ish feel)
    >>> ax.set_xlabel("X (index)")
    >>> set_top_ylabel(ax, "log(scale) + perturbation", fontsize=14, fontweight="bold")
    >>> ax.set_title("Stata-like plotplainblind styling with on-line labels")
    >>>
    >>> # 6) Optional cosmetics
    >>> ax.margins(x=0.02)
    >>> plt.tight_layout()
    >>> plt.show()
    """
    
    colors = [
        "#000000",  # black
        "#9E9E9E",  # gray
        "#4DA3FF",  # light blue
        "#00A087",  # teal
        "#CC79A7",  # pink
        "#E69F00",  # orange
        "#0072B2",  # dark blue
        "#E69F00",  # gold-ish (repeat ok for long cycles)
        "#F0E442",  # yellow
        "#BDBDBD",  # light gray
    ]

    linestyles = [
        "-",                # solid
        (0, (6, 4)),        # dashed
        (0, (1, 2)),        # dotted
        (0, (1, 3, 4, 3)),  # dotdash-ish
        (0, (4, 2, 1, 2)),  # dashdot-ish
        (0, (3, 2)),        # shortdash
        "-",                # repeat
        (0, (4, 2, 1, 2)),
        (0, (3, 2)),
        (0, (8, 4)),        # longdash
    ]

    markers = ["o", "s", "D", "^", "+", "x", "o", "D", "s", "^"]

    mpl.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#9E9E9E",
        "axes.linewidth": 1.2,
        "axes.spines.top": False,
        "axes.spines.right": False,

        "axes.grid": True,
        "axes.grid.axis": "both",
        "grid.color": "#BDBDBD",
        "grid.linestyle": (0, (1, 4)),  # dotted grid
        "grid.linewidth": 1.0,

        "xtick.color": "#9E9E9E",
        "ytick.color": "#9E9E9E",
        "xtick.labelcolor": "black",
        "ytick.labelcolor": "black",

        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 13,
        "axes.titlesize": 20,
        "axes.labelsize": 18,

        "lines.linewidth": 3.0,
        "lines.markersize": 7,

        "legend.frameon": False,
        "legend.fontsize": 14,
    })

    if kind == "line":
        mpl.rcParams["axes.prop_cycle"] = cycler(color=colors) + cycler(linestyle=linestyles)
    elif kind == "scatter":
        mpl.rcParams["axes.prop_cycle"] = cycler(color=colors) + cycler(marker=markers)
    elif kind == "connected":
        mpl.rcParams["axes.prop_cycle"] = (
            cycler(color=colors) + cycler(linestyle=linestyles) + cycler(marker=markers)
        )
    elif kind == "mono":
        mpl.rcParams["axes.prop_cycle"] = cycler(color=["#4D4D4D"])
    else:
        raise ValueError("kind must be one of: line, scatter, connected, mono")
