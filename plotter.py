import matplotlib.pyplot as plt
import numpy as np

# Data
labels = ["CK8", "COL1A1", "COL3A1", "ELN", "Ki67", "SMA", "SMTN", "UPK2"]
means = [0.682121547, 3.556771411, 1.030590035, 1.621001522,
         1.042606414, 1.109064498, 1.104165846, 1.454265511]
std_dev = [0.180270134, 1.100294255, 0.30704668, 0.7307007,
           0.371506819, 0.129199057, 0.654008534, 0.437220306]

x = np.arange(len(labels))

# Create figure
fig, ax = plt.subplots(figsize=(8, 6))

# Bars (Prism style: white fill, black border, thicker lines)
bars = ax.bar(
    x,
    means,
    yerr=std_dev,
    width=0.7,
    color="white",
    edgecolor="black",
    linewidth=2,
    capsize=6,
    error_kw=dict(elinewidth=2, capthick=2, ecolor="black")
)

# Axis formatting (Prism style)
ax.set_ylabel("Fold Change", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=12)
ax.tick_params(axis='y', labelsize=12, width=1.5)
ax.tick_params(axis='x', width=1.5)

# Remove top and right spines (Prism default)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Thicken remaining spines
ax.spines["left"].set_linewidth(2)
ax.spines["bottom"].set_linewidth(2)

# Set y-axis to start at zero
ax.set_ylim(0, max(means) + max(std_dev) + 0.5)

# Remove grid
ax.grid(False)

# Tight layout for clean margins
plt.tight_layout()

# High resolution export option
plt.savefig("Prism_style_bargraph.tiff", dpi=600, bbox_inches="tight")

plt.show()
