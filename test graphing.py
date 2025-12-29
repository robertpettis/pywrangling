import numpy as np
import matplotlib.pyplot as plt

# Import your helpers from the installed package
from pywrangling.graphing_functions import (
    use_plotplainblind_matched,
    label_line,
    set_top_ylabel,
)

# ------------------------------------------------------------
# 1) Apply Stata-like style + cycle logic
# ------------------------------------------------------------
use_plotplainblind_matched(kind="connected")

# ------------------------------------------------------------
# 2) Fake data: three series with different shapes
# ------------------------------------------------------------
x = np.arange(1, 25)
y_a = np.log(x) + 0.08 * np.sin(x)
y_b = np.log(x) - 0.25 + 0.06 * np.cos(1.2 * x)
y_c = np.log(x) - 0.50 + 0.04 * np.sin(0.7 * x + 1.0)

# ------------------------------------------------------------
# 3) Build figure
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.5))

# ------------------------------------------------------------
# 4) Plot + label each line directly (no legend needed)
# ------------------------------------------------------------
label_line(ax, x, y_a, "Series A", prefer="whitespace")
label_line(ax, x, y_b, "Series B", prefer="whitespace")
label_line(ax, x, y_c, "Series C", prefer="whitespace")

# ------------------------------------------------------------
# 5) Axis labeling (y label on top, Stata-ish feel)
# ------------------------------------------------------------
ax.set_xlabel("X (index)")
set_top_ylabel(ax, "log(scale)\n+ perturbation", fontsize=14, fontweight="bold")
ax.set_title("Stata-like plotplainblind styling with on-line labels")

# ------------------------------------------------------------
# 6) Optional cosmetics
# ------------------------------------------------------------
ax.margins(x=0.02)
plt.tight_layout()
plt.show()
